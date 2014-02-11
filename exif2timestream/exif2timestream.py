from csv import reader, DictReader
import exifread as er
import os
from os import path
import shutil
from sys import exit, stdout
from time import strptime, strftime, mktime, localtime, struct_time, time
from voluptuous import Required, Schema, MultipleInvalid
from itertools import cycle
from inspect import isclass
import logging


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
    exif2timestream.py [-t PROCESSES -1 -l LOGDIR] -c CAM_CONFIG_CSV
    exif2timestream.py -g CAM_CONFIG_CSV

OPTIONS:
    -1                  Use one core
    -t PROCESSES        Number of processes to use.
    -l LOGDIR           Directory to contain log files. [Default:  .]
    -c CAM_CONFIG_CSV   Path to CSV camera config file for normal operation.
    -g CAM_CONFIG_CSV   Generate a template camera configuration file at given
                        path.
"""


# Sort out logging.
NOW = strftime("%Y%m%dT%H%M", localtime())
LOG = logging.getLogger("exif2timestream")


# Map csv fields to camera dict fields. Should be 1 to 1, but is here for
# compability.
FIELDS = {
    'use': 'USE',
    'name': 'CAMERA_NAME',
    'location': 'LOCATION',
    'expt': 'CURRENT_EXPT',
    'source': 'SOURCE',
    'destination': 'DESTINATION',
    'archive_dest': 'ARCHIVE_DEST',
    'expt_end': 'EXPT_END',
    'expt_start': 'EXPT_START',
    'interval': 'INTERVAL',
    'image_types': 'IMAGE_TYPES',
    'method': 'METHOD',
    'resolutions': 'resolutions',
    'sunrise': 'sunrise',
    'sunset': 'sunset',
    'timezone': 'camera_timezone',
    'user': 'user',
    'mode': 'mode',
}

FIELD_ORDER = [
    'use',
    'name',
    'location',
    'expt',
    'source',
    'destination',
    'archive_dest',
    'expt_start',
    'expt_end',
    'interval',
    'image_types',
    'method',
    'resolutions',
    'sunrise',
    'sunset',
    'timezone',
    'user',
    'mode',
]

class SkipImage(StopIteration):

    """
    Exception that specifically means skip this image.

    Allows try-except blocks to pass any errors on to the calling functions,
    unless they can be solved by skipping the erroring image.
    """
    pass


def validate_camera(camera):
    """Validates and converts to python types the given camera dict (which
    normally has string values).
    """
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
            return (int(x) // 100, int(x) % 100)

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
                res_list.append((x, y))
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
        Required(FIELDS["use"]): bool_str,
        Required(FIELDS["destination"]): path_exists,
        Required(FIELDS["expt"]): str,
        Required(FIELDS["expt_end"]): date,
        Required(FIELDS["expt_start"]): date,
        Required(FIELDS["image_types"]): image_type_str,
        Required(FIELDS["interval"], default=1): num_str,
        Required(FIELDS["location"]): str,
        Required(FIELDS["archive_dest"]): path_exists,
        Required(FIELDS["method"], default="archive"): \
            InList(["copy", "archive", "move"]),
        Required(FIELDS["name"]): str,
        Required(FIELDS["source"]): path_exists,
        FIELDS["mode"]: InList(["batch", "watch"]),
        FIELDS["resolutions"]: resolution_str,
        FIELDS["user"]: str,
        FIELDS["sunrise"]: int_time_hr_min,
        FIELDS["sunset"]: int_time_hr_min,
        FIELDS["timezone"]: int_time_hr_min,
    })
    try:
        cam = sch(camera)
        LOG.debug("Validated camera '{0:s}'".format(cam))
        return cam
    except MultipleInvalid as e:
        if camera[FIELDS["use"]] != '0':
            raise e
        return None


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
    LOG.debug("Date of '{0:s}' is '{1:s}'".format(filename, date))
    return date


def get_new_file_name(date_tuple, ts_name, n=0, fmt=TS_FMT, ext="jpg"):
    """
    Gives the new file name for an image within a timestream, based on
    datestamp, timestream name, sub-second series count and extension.
    """
    if date_tuple is None or not date_tuple:
        LOG.error("Must supply get_new_file_name with a valid date." +
                  "Date is '{0:s}'".format(date_tuple))
        raise ValueError("Must supply get_new_file_name with a valid date.")
    if not ts_name:
        LOG.error("Must supply get_new_file_name with timestream name." +
                  "TimeStream name is '{0:s}'".format(ts_name))
        raise ValueError("Must supply get_new_file_name with timestream name.")
    date_formatted_name = strftime(fmt, date_tuple)
    name = date_formatted_name.format(tsname=ts_name, n=n, ext=ext)
    LOG.debug("New filename is '{0:s}'".format(name))
    return name


def round_struct_time(in_time, round_secs, tz_hrs=0, uselocal=True):
    """
    Round a struct_time object to any time interval in seconds
    """
    seconds = mktime(in_time)
    rounded = int(round(seconds / float(round_secs)) * round_secs)
    if not uselocal:
        rounded -= tz_hrs * 60 * 60  # remove tz seconds, back to UTC
    retval = localtime(rounded)
    # This is hacky as fuck. We need to replace stuff from time module with
    # stuff from datetime, which actually fucking works.
    rv_list = list(retval)
    rv_list[8] = in_time.tm_isdst
    rv_list[6] = in_time.tm_wday
    retval = struct_time(tuple(rv_list))
    LOG.debug("time {0:s} rounded to {1:d} seconds is {2:s}".format(
        in_time, round_secs, retval))
    return retval


def make_timestream_name(camera, res="fullres", step="orig"):
    """
    Makes a timestream name given the format (module-level constant), step,
    resolution and a camera object.
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


def timestreamise_image(image, camera, subsec=0, step="orig"):
    """Process a single image, mv/cp-ing it to its new location"""
    # make new image path
    image_date = get_file_date(image, camera[FIELDS["interval"]] * 60)
    if not image_date:
        raise SkipImage
    in_ext = path.splitext(image)[-1].lstrip(".")
    ts_name = make_timestream_name(camera, res="fullres", step=step)
    out_image = get_new_file_name(
        image_date,
        ts_name,
        n=subsec,
        ext=in_ext
    )
    out_image = path.join(
        camera[FIELDS["destination"]],
        camera[FIELDS["expt"]],
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
            LOG.warn("Could not make dir '{0:s}', skipping image '{1:s}'".format(
                out_dir, image))
            raise SkipImage
    # And do the copy
    dest = _dont_clobber(out_image, mode=SkipImage)
    try:
        shutil.copy(image, dest)
        LOG.info("Copied '{0:s}' to '{1:s}".format(image, dest))
    except Exception as e:
        LOG.warn("Could copy '{0:s}' to '{1:s}', skipping image".format(
            image, dest))
        raise SkipImage


def _dont_clobber(fn, mode="append"):
    """Ensure we don't overwrite things, using a variety of methods"""
    if path.exists(fn):
        # Deal with SkipImage or StopIteration exceptions
        if isinstance(mode, StopIteration):
            LOG.debug("Path '{0}' exists, raising an Exception".format(fn))
            raise mode
        # Ditto, but if we pass them uninstantiated
        elif isclass(mode) and issubclass(mode, StopIteration):
            LOG.debug("Path '{0}' exists, raising an Exception".format(fn))
            raise mode()
        # Otherwise, append something '_1' to the file name to solve our
        # problem
        elif mode == "append":
            LOG.debug("Path '{0}' exists, adding '_1' to its name".format(fn))
            base, ext = path.splitext(fn)
            # append _1 to filename
            if ext != '':
                return ".".join(["_".join([base, "1"]), ext])
            else:
                return "_".join([base, "1"])
        else:
            raise ValueError("Bad _dont_clobber mode: %r", mode)
    else:
        # Doesn't exist, so return good path
        LOG.debug("Path '{0}' doesn't exist. Returning it.".format(fn))
        return fn


def process_image(args):
    """
    Given a camera config and list of images, will do the required
    move/copy operations.
    """
    (image, camera, ext) = args
    stdout.write(".")
    stdout.flush()

    image_date = get_file_date(image, camera[FIELDS["interval"]] * 60)
    if image_date < camera[FIELDS["expt_start"]] or \
            image_date > camera[FIELDS["expt_end"]]:
        return  # Don't raise SkipImage as it isn't caught

    # archive a backup before we fuck anything up
    if camera[FIELDS["method"]] == "archive":
        ts_name = make_timestream_name(camera, res="fullres")
        archive_image = path.join(
            camera[FIELDS["archive_dest"]],
            camera[FIELDS["expt"]],
            ts_name,
            path.basename(image)
        )
        archive_dir = path.dirname(archive_image)
        if not path.exists(archive_dir):
            os.makedirs(archive_dir)
        archive_image = _dont_clobber(archive_image)
        shutil.copy2(image, archive_image)
    # TODO: BUG: this won't work if images aren't in chronological order. Which
    # they never will be.
    # if last_date == image_date:
    # increment the sub-second counter
    #    subsec += 1
    # else:
    # we've moved to the next time, so 0-based subsec counter == 0
    if ext.lower() == "raw" or ext.lower() in RAW_FORMATS:
        step = "raw"
    else:
        step = "orig"
    subsec = 0
    try:
        # deal with original image (move/copy etc)
        timestreamise_image(image, camera, subsec=subsec, step=step)
    except SkipImage:
        return
    if camera[FIELDS["method"]] in {"move", "archive"}:
        # images have already been archived above, so just delete originals
        try:
            os.unlink(image)
        except os.error as e:
            LOG.error("Could not delete '{0}'".format(image))


def get_local_path(this_path):
    """Replaces slashes of any kind for the correct kind for the local system"""
    return this_path.replace("/", path.sep).replace("\\", path.sep)


def localise_cam_config(camera):
    """Make camera use localised settings, e.g. path separators"""
    if camera is None:
        return None
    camera[FIELDS["source"]] = get_local_path(camera[FIELDS["source"]])
    camera[FIELDS["archive_dest"]] = get_local_path(
        camera[FIELDS["archive_dest"]])
    camera[FIELDS["destination"]] = get_local_path(
        camera[FIELDS["destination"]])
    return camera


def parse_camera_config_csv(filename):
    """
    Parse a camera configuration CSV.
    It yields localised, validated camera dicts
    """
    fh = open(filename)
    cam_config = DictReader(fh)
    for camera in cam_config:
        camera = validate_camera(camera)
        camera = localise_cam_config(camera)
        if camera is not None and camera[FIELDS["use"]]:
            yield camera


def find_image_files(camera):
    """
    Scrape a directory for image files, by extension.
    Possibly, in future, use file magic numbers, but a bad idea on windows.
    """
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
                for d in dirs:
                    if not d.startswith("_"):
                        LOG.error("Souce directory has too many subdirs.A")
                        # TODO: Is raising here a good idea?
                        #raise ValueError("too many subdirs")
            for fle in files:
                this_ext = path.splitext(fle)[-1].lower().strip(".")
                if this_ext == ext or ext == "raw" and this_ext in RAW_FORMATS:
                    fle_path = path.join(cur_dir, fle)
                    try:
                        ext_files[ext].append(fle_path)
                    except KeyError:
                        ext_files[ext] = []
                        ext_files[ext].append(fle_path)
            LOG.info("Found {0} {1} files for camera {2}.".format(
                len(files),
                ext,
                camera[FIELDS["name"]]))
    return ext_files


def generate_config_csv(filename):
    """Make a config csv template"""
    with open(filename, "w") as fh:
        fh.write(",".join([FIELDS[x] for x in FIELD_ORDER]))
        fh.write("\n")


def main(opts):
    """The main loop of the module, do the renaming in parallel etc."""
    if opts['-g'] is not None:
        # No logging when we're just generating a config file. What could
        # possibly go wrong...
        null = logging.NullHandler()
        LOG.addHandler(null)
        generate_config_csv(opts["-g"])
        exit()
    # we want logging for the real main loop
    fmt = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(fmt)
    logdir = opts['-l']
    if not path.exists(logdir):
        logdir = "."
    fh = logging.FileHandler(path.join(logdir, "e2t_" + NOW + ".log"))
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    LOG.addHandler(fh)
    LOG.addHandler(ch)
    # beginneth the actual main loop
    start_time = time()
    cameras = parse_camera_config_csv(opts["-c"])
    n_images = 0
    for camera in cameras:
        print "Processing camera {0}".format(camera[FIELDS["name"]])
        LOG.info("Processing camera {0}".format(camera[FIELDS["name"]]))
        for ext, images in find_image_files(camera).iteritems():
            images = sorted(images)
            n_cam_images = len(images)
            print "{0} {1} images from this camera".format(n_cam_images, ext)
            LOG.info("Have {0} {1} images from this camera".format(
                n_cam_images, ext))
            n_images += n_cam_images
            last_date = None
            subsec = 0
            # TODO: sort out the whole subsecond clusterfuck
            if "-1" in opts and opts["-1"]:
                LOG.info("using 1 process (What is this? Fucking 1990?)")
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
                LOG.info("Using {0:d} processes".format(threads))
                # set the function's camera-wide arguments
                args = zip(images, cycle([camera]), cycle([ext]))
                pool = Pool(threads)
                pool.map(process_image, args)
                pool.close()
                pool.join()
    secs_taken = time() - start_time
    print "\nProcessed a total of {0} images in {1:.2f} seconds".format(
        n_images, secs_taken)


if __name__ == "__main__":
    from docopt import docopt
    opts = docopt(CLI_OPTS)
    # lets do this shit.
    main(opts)
else:
    # No logging for test/when imported
    null = logging.NullHandler()
    LOG.addHandler(null)
