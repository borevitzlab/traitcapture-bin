from csv import reader, DictReader
import exifread as er
import os
from os import path
import shutil
from sys import exit, stdout
from time import strptime, strftime, mktime, localtime, struct_time
from voluptuous import Required, Schema
from itertools import cycle
from inspect import isclass


EXIF_DATE_TAG = "Image DateTime"
EXIF_DATE_FMT = "%Y:%m:%d %H:%M:%S"

TS_V1_FMT = ("%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/"
             "{tsname:s}_%Y_%m_%d_%H_%M_%S_{n:02d}.{ext:s}")
TS_V2_FMT = ("%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/"
             "{tsname:s}_%Y_%m_%d_%H_%M_%S_{n:02d}.{ext:s}")
TS_FMT = TS_V1_FMT

TS_NAME_FMT = "{expt:s}-{loc:s}-{cam:s}~{res:s}-{step:s}"

FULLRES_CONSTANTS = {"original", "orig", "fullres"}
IMAGE_TYPE_CONSTANTS = {"raw", "jpg"}

RAW_FORMATS = {"cr2", "nef", "tif", "tiff"}

CLI_OPTS = """
USAGE:
    exif2timestream.py [-t PROCESSES -1] -c CAM_CONFIG_CSV
    exif2timestream.py -g CAM_CONFIG_CSV

OPTIONS:
    -1                  Use one core
    -t PROCESSES        Number of processes to use. Defaults to 1
    -c CAM_CONFIG_CSV   Path to CSV camera config file for normal operation.
    -g CAM_CONFIG_CSV   Generate a template camera configuration file at given
                        path.
"""

class SkipImage(StopIteration):
    pass

# Map csv fields to camera dict fields. Should be 1 to 1, but is here for
# compability
FIELDS = {
        'archive_dest': 'archive_dest',
        'destination': 'destination',
        'expt': 'current_expt',
        'expt_end': 'expt_end',
        'expt_start': 'expt_start',
        'image_types': 'image_types',
        'interval': 'interval',
        'location': 'location',
        'method': 'method',
        'mode': 'mode',
        'name': 'camera_name_f',
        'resolutions': 'resolutions',
        'source': 'source',
        'sunrise': 'sunrise',
        'sunset': 'sunset',
        'timezone': 'camera_timezone',
        'use': 'use',
        'user': 'user'
        }


def validate_camera(camera):
    def date(x):
        if isinstance(x, struct_time):
            return x
        else:
            try:
               return strptime(x, "%Y_%m_%d")
            except:
                raise ValueError

    num_str = lambda x: int(x)

    def bool_str(x):
        if isinstance(x, bool):
            return x
        elif isinstance(x, int):
            return bool(int(x))
        elif isinstance(x, str):
            x = x.strip().lower()
            try:
                return bool(int(x))
            except:
                if x in {"t", "true", "y", "yes", "f", "false", "n", "no"}:
                    return x in {"t", "true", "y", "yes"}
        raise ValueError

    def int_time_hr_min(x):
        if isinstance(x, tuple):
            return x
        else:
            return (int(x)//100, int(x) % 100 )
    def path_exists(x):
        if path.exists(x):
            return x
        else:
            raise ValueError("path '%s' doesn't exist" % x)

    def resolution_str(x):
        if not isinstance(x, str):
            raise ValueError
        xs = x.strip().split('~')
        res_list = []
        for res in xs:
            # First, attempt splitting into X and Y components. Non <X>x<Y>
            # resolutions will be returned as a single item in a list,
            # hence the len(xy) below
            xy = res.strip().lower().split("x")
            if res in FULLRES_CONSTANTS:
                res_list.append(res)
            elif len(xy) == 2:
                # it's an XxY thing, hopefully
                x, y = xy
                x, y = int(x), int(y)
                res_list.append((x,y))
            else:
                # we'll pretend it's an int, for X resolution, and any ValueError
                # triggered here will be propagated to the vaildator
                res_list.append((int(res), None))
        return res_list

    def image_type_str(x):
        if isinstance(x, list):
            return x
        if not isinstance(x, str):
            raise ValueError
        types = x.lower().strip().split('~')
        for type in types:
            if not type in IMAGE_TYPE_CONSTANTS:
                raise ValueError
        return types

    class InList(object):
        def __init__(self, valid_values):
            if isinstance(valid_values, list) or \
                    isinstance(valid_values, tuple):
                self.valid_values = set(valid_values)
        def __call__(self, x):
            if not x in self.valid_values:
                raise ValueError
            return x

    sch = Schema({
        Required(FIELDS["destination"]): path_exists,
        Required(FIELDS["expt"]): str,
        Required(FIELDS["expt_end"]): date,
        Required(FIELDS["expt_start"]): date,
        Required(FIELDS["image_types"]): image_type_str,
        Required(FIELDS["interval"], default=1): num_str,
        Required(FIELDS["location"]): str,
        Required(FIELDS["method"], default="archive"): InList(["copy", "archive",
            "move"]),
        Required(FIELDS["mode"], default="batch"): InList(["batch", "watch"]),
        # watch not implemented yet though
        Required(FIELDS["name"]): str,
        Required(FIELDS["resolutions"], default="fullres"): resolution_str,
        Required(FIELDS["source"]): path_exists,
        Required(FIELDS["use"]): bool_str,
        Required(FIELDS["user"]): str,
        FIELDS["archive_dest"]: path_exists,
        FIELDS["sunrise"]: int_time_hr_min,
        FIELDS["sunset"]: int_time_hr_min,
        FIELDS["timezone"]: int_time_hr_min,
        })
    cam = sch(camera)
    return cam


def get_file_date(filename, round_secs=1):
    """
    Gets a time.struct_time from an image's EXIF, or None if not possible.
    """
    with open(filename, "rb") as fh:
        exif_tags = er.process_file(fh, details=False, stop_tag=EXIF_DATE_TAG)
    try:
        str_date = exif_tags[EXIF_DATE_TAG].values
        date = strptime(str_date, EXIF_DATE_FMT)
    except KeyError:
        return None
    if round_secs > 1:
        date = round_struct_time(date, round_secs)
    return date


def get_new_file_name(date_tuple, ts_name, n=0, fmt=TS_FMT, ext="jpg"):
    """
    Gives the new file name for an image within a timestream, based on
    datestamp, timestream name, sub-second series count and extension.
    """
    if date_tuple is None or not date_tuple:
        raise ValueError("Must supply get_new_file_name with a valid date")
    if not ts_name:
        raise ValueError("Must supply get_new_file_name with timestream name")
    date_formatted_name = strftime(fmt, date_tuple)
    name = date_formatted_name.format(tsname=ts_name, n=n, ext=ext)
    return name


def round_struct_time(in_time, round_secs, tz_hrs=0, uselocal=True):
    """
    Round a struct_time object to any time interval in seconds
    """
    seconds = mktime(in_time)
    rounded = int(round(seconds / float(round_secs)) * round_secs)
    if not uselocal:
        rounded -= tz_hrs * 60 * 60 # remove tz seconds, back to UTC
    retval = localtime(rounded)
    # This is hacky as fuck. We need to replace stuff from time module with
    # stuff from datetime, which actually fucking works.
    rv_list = list(retval)
    rv_list[8] = in_time.tm_isdst
    rv_list[6] = in_time.tm_wday
    retval = struct_time(tuple(rv_list))
    return retval


def make_timestream_name(camera, res="fullres", step="orig"):
    """
    "{expt:s}-{loc:s}-{cam:s}~{res:s}-{step:s}"
    """
    if isinstance(res, tuple):
        res = "x".join([str(x) for x in res])
    # raise ValueError(str((camera, res, step)))
    return TS_NAME_FMT.format(
            expt=camera[FIELDS["expt"]],
            loc=camera[FIELDS["location"]],
            cam=camera[FIELDS["name"]],
            res=res,
            step=step
            )


def timestreamise_image(image, camera, subsec=0):
    # make new image path
    image_date = get_file_date(image, camera[FIELDS["interval"]] * 60)
    if not image_date:
        raise SkipImage
    in_ext = path.splitext(image)[-1].lstrip(".")
    ts_name = make_timestream_name(camera, res="fullres")
    out_image = get_new_file_name(
        image_date,
        ts_name,
        n=subsec,
        ext=in_ext
        )
    out_image = path.join(
        camera[FIELDS["destination"]],
        ts_name,
        out_image
        )
    # make the target directory
    out_dir = path.dirname(out_image)
    if not path.exists(out_dir):
        # makedirs is like `mkdir -p`, creates parents, but raises
        # os.error if target already exits
        try:
            os.makedirs(out_dir)
        except os.error:
            raise SkipImage
    # And do the copy
    try:
        shutil.copy(image, _dont_clobber(out_image, mode=SkipImage))
    except Exception as e:
        raise SkipImage


def _dont_clobber(fn, mode="append"):
    if path.exists(fn):
        if isinstance(mode, Exception):
            raise mode
        elif isclass(mode) and issubclass(mode, StopIteration):
            raise mode()
        elif mode == "append":
            base, ext = path.splitext(fn)
            # append _1 to filename
            if ext != '':
                return ".".join(["_".join([base, "1"]), ext])
            else:
                return "_".join([base, "1"])
        else:
            raise ValueError("Bad _dont_clobber mode: %r", mode)
    else:
        return fn

def process_image((image, camera, ext)):
    """
    Given a camera config and list of images, will do the required
    move/copy operations.
    """
    stdout.write(".")
    stdout.flush()
    # archive a backup before we fuck anything up
    if camera[FIELDS["method"]] == "archive":
        archive_image = path.join(
                camera[FIELDS["archive_dest"]],
                path.basename(image)
                )
        if not path.exists(camera[FIELDS["archive_dest"]]):
            os.makedirs(camera[FIELDS["archive_dest"]])
        archive_image = _dont_clobber(archive_image)
        shutil.copy2(image, archive_image)
    #TODO: BUG: this won't work if images aren't in chronological order. Which
    # they never will be.
    #if last_date == image_date:
    #    # increment the sub-second counter
    #    subsec += 1
    #else:
    #    # we've moved to the next time, so 0-based subsec counter == 0
    subsec = 0
    try:
        # deal with original image (move/copy etc)
        timestreamise_image(image, camera, subsec=subsec)
    except SkipImage:
       return
    if camera[FIELDS["method"]] in {"move", "archive"}:
        # images have already been archived above, so just delete originals
        os.unlink(image)


def get_local_path(this_path):
    return this_path.replace("/", path.sep).replace("\\", path.sep)


def localise_cam_config(camera):
    camera[FIELDS["source"]] = get_local_path(camera[FIELDS["source"]])
    camera[FIELDS["archive_dest"]] = \
          get_local_path(camera[FIELDS["archive_dest"]])
    camera[FIELDS["destination"]] = get_local_path(camera[FIELDS["destination"]])
    return camera


def parse_camera_config_csv(filename):
    fh = open(filename)
    cam_config = DictReader(fh)
    for camera in cam_config:
        camera = localise_cam_config(camera)
        camera = validate_camera(camera)
        if camera[FIELDS["use"]]:
            yield camera

def find_image_files(camera):
    exts = camera[FIELDS["image_types"]]
    ext_files = {}
    for ext in exts:
        if ext.lower() in RAW_FORMATS:
            ext_dir = "raw"
        else:
            ext_dir = ext
        src = path.join(camera[FIELDS["source"]], ext_dir)
        walk = os.walk(src, topdown=True)
        for cur_dir, dirs, files in walk:
            if len(dirs) > 0:
                #TODO: Accept extra directories if they start w/ '_'
                raise ValueError("too many subdirs")
            for fle in files:
                this_ext = path.splitext(fle)[-1].lower().strip(".")
                if this_ext == ext:
                    fle_path = path.join(cur_dir, fle)
                    try:
                        ext_files[ext].append(fle_path)
                    except KeyError:
                        ext_files[ext] = []
                        ext_files[ext].append(fle_path)
    return ext_files



def generate_config_csv(filename):
    with open(filename, "w") as fh:
        fh.write(",".join([x for x in sorted(FIELDS.values())]))
        fh.write("\n")


def main(opts):
    if "-g" in opts and opts['-g'] is not None:
        generate_config_csv(opts["-g"])
        exit()
    cameras = parse_camera_config_csv(opts["-c"])
    n_images = 0
    for camera in cameras:
        for ext, images in find_image_files(camera).iteritems():
            images = sorted(images)
            n_images += len(images)
            last_date = None
            subsec = 0
            #TODO: sort out the whole subsecond clusterfuck
            if "-1" in opts and opts["-1"]:
                print "using 1 thread"
                #TODO test for this block
                for image in images:
                    process_image((image, camera, ext))
            else:
                from multiprocessing import Pool, cpu_count
                if "-t" in opts and opts["-t"] is not None:
                    try:
                        threads = int(opts["-t"])
                    except ValueError:
                        threads = cpu_count() - 1
                else:
                    threads = cpu_count() - 1
                print "using %i threads" % threads
                # set the function's camera-wide arguments
                args = zip(images, cycle([camera]), cycle([ext]))
                pool = Pool(threads)
                pool.map(process_image, args)
                pool.close()
                pool.join()
    print # add a newline


if __name__ == "__main__":
    from docopt import docopt
    opts = docopt(CLI_OPTS)
    main(opts)
