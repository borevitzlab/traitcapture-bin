import ConfigParser as configparser
from csv import reader, DictReader
from docopt import docopt
import exifread as er
import os
from os import path
from PIL import Image
import shutil
from sys import exit
from time import strptime, strftime, mktime, localtime

EXIF_DATE_TAG = "Image DateTime"
EXIF_DATE_FMT = "%Y:%m:%d %H:%M:%S"

TS_V1_FMT = ("%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/"
             "{tsname:s}_%Y_%m_%d_%H_%M_%S_{n:02d}.{ext:s}")
TS_V2_FMT = ("%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/"
             "{tsname:s}_%Y_%m_%d_%H_%M_%S_{n:02d}.{ext:s}")
TS_FMT = TS_V1_FMT

TS_NAME_FMT = "{expt:s}-{loc:s}-{cam:s}~{res:s}-{step:s}"

RAW_FORMATS = {"cr2", "nef", "tif", "tiff"}

CLI_OPTS = """
USAGE:
    exif2timestream.py [-a ARCHIVE_DIR] -c CAM_CONFIG_CSV
    exif2timestream.py -g CAM_CONFIG_CSV

OPTIONS:
    -a ARCHIVE_DIR      Directory to archive processed photos to when action is
                        "archive".
    -c CAM_CONFIG_CSV   Path to CSV camera config file for normal operation.
    -g CAM_CONFIG_CSV   Generate a template camera configuration file at given
                        path.
"""

# Map csv fields to camera dict fields. Should be 1 to 1, but is here for
# compability
FIELDS = {
        'archive_dest': 'archive_dest',
        'destination': 'destination',
        'expt': 'current_expt',
        'expt_end': 'expt_end',
        'expt_start': 'expt_start',
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
    if round_secs > 0:
        round_struct_time(date, round_secs)
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


def resize_image(dest_fn, src_fn, x, y, fmt="JPEG", keep_aspect=False,
        crop=False):
    """
    Resize image and write it out.
    """
    im = Image.open(src_fn)
    if keep_aspect:
        im.thumbnail((x, y), Image.ANTIALIAS)
    else:
        if crop:
            raise NotImplementedError("Crop-based resizing not implemented")
        else:
            im = im.resize((x, y), Image.ANTIALIAS)
    im.save(dest_fn, fmt)
    return im


def round_struct_time(in_time, round_secs, tz_hrs=0, uselocal=True):
    """
    Round a struct_time object to any time lapse in seconds
    """
    seconds = mktime(in_time)
    rounded = int(round(seconds / float(round_secs)) * round_secs)
    if not uselocal:
        rounded -= tz_hrs * 60 * 60 # remove tz seconds, back to UTC
    return localtime(rounded)


def make_timestream_name(camera, res="fullres", step="orig"):
    """
    "{expt:s}-{loc:s}-{cam:s}~{res:s}-{step:s}"
    """
    return TS_NAME_FMT.format(
            expt=camera[FIELDS["expt"]],
            loc=camera[FIELDS["location"]],
            cam=camera[FIELDS["name"]],
            res=res,
            step=step
            )


def do_image_resizing(image, camera, subsec=0, keep_aspect=False,
        crop=False):
    # get a list of resolutions to down-size to, as text
    resolutions = camera[FIELDS["resolutions"]].strip().split('~')
    in_ext = path.splitext(image)[-1].lstrip(".")
    image_date = get_file_date(image)
    for resolution in resolutions:
        bad_res = False
        # attempt splitting into X and Y components. non <X>x<Y>
        # resolutions will be returned as a single item in a list, hence
        # the len(xy) below
        xy = resolution.lower().strip().split("x")
        if resolution.strip().lower() in {"original", "orig", "fullres"}:
            # the fullres image is done below. so we skip the copy/move bit
            # for now, ensuring we can be lazy about specifiying the source
            # of resized images
            pass
        elif len(xy) == 2:
            # it's an NxN size spec, so resize
            x, y = xy
            try:
                x = int(x)
                y = int(y)
            except ValueError:
                bad_res = True
            resized_name = make_timestream_name(camera, res=resolution)
            resized_image = get_new_file_name(image_date, resized_name,
                    n=subsec, ext=in_ext)
            resized_image = path.join(
                camera[FIELDS["destination"]],
                resized_name,
                resized_image
                )

            out_dir = path.dirname(resized_image)
            if not path.exists(out_dir):
                # makedirs is like `mkdir -p`, creates parents, but raises
                # os.error if target already exits
                os.makedirs(out_dir)
                #TODO: implement try/except. for now, just let the error crash it

            resize_image(resized_image, image, x, y, keep_aspect=keep_aspect,
                    crop=crop)
            #TODO
        else:
            # something's screwy. raise an error
            bad_res = True

        if bad_res:
            raise ValueError(
                    "Camera {cam:s}: bad resolution of'{res:s}'".format(
                        cam=camera[FIELDS["name"]], res=camera[FIELDS["resolutions"]])
                    )


def timestreamise_image(image, camera, subsec=0):
    # make new image path
    image_date = get_file_date(image)
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
        os.makedirs(out_dir)
        #TODO: implement try/except. for now, just let the error crash it

    #try:
    shutil.copy(image, out_image)
    #except Exception as e:
    #TODO: implment proper try/except. for now, just let the error crash it


def process_camera_images(images, camera):
    """
    Given a camera config and list of images, will do the required
    move/copy/resize operations.
    """
    last_date = None
    subsec = 0
    for image in images:
        # archive a backup before we fuck anything up
        if camera[FIELDS["method"]] == "archive":
            archive_image = path.join(
                    camera[FIELDS["archive_dest"]],
                    path.basename(image)
                    )
            if not path.exists(camera[FIELDS["archive_dest"]]):
                os.makedirs(camera[FIELDS["archive_dest"]])
            shutil.copy2(image, archive_image)

        image_date = get_file_date(image)
        if last_date == image_date:
            # increment the sub-second counter
            subsec += 1
        else:
            # we've moved to the next time, so 0-based subsec counter == 0
            subsec = 0

        # do the resizing of images
        do_image_resizing(image, camera)
        # deal with original image (move/copy etc)
        timestreamise_image(image, camera, subsec=subsec)

        if camera[FIELDS["method"]] in {"move", "archive"}:
            # images have already been archived above, so just delete originals
            os.unlink(image)



def get_local_path(this_path):
    return this_path.replace("/", path.sep).replace("\\", path.sep)

def localise_cam_config(camera):
    camera[FIELDS["source"]] = get_local_path(camera[FIELDS["source"]])
    camera[FIELDS["destination"]] =  get_local_path(camera[FIELDS["destination"]])
    return camera

def parse_camera_config_csv(filename):
    fh = open(filename)
    cam_config = DictReader(fh)
    to_move = {}

    # check header
    header = set(cam_config.fieldnames)
    expct_header = set(FIELDS.values())
    for item in header:
        if item not in expct_header:
            raise ValueError("Bad config CSV: Extraneous field '{0}'".format(item))
    for item in expct_header:
        if item not in header:
            raise ValueError("Bad config CSV: Missing field '{0}'".format(item))

    for camera in cam_config:
        camera = localise_cam_config(camera)
        #TODO: do a check that all values of FIELDS exist and have valid values
        # in this camera

        cam_to_move = {}
        # work out if we should skip this cam
        try:
            # csv parser gives a string, which may or may not have some
            # whitespace padding around it, which strip() removes
            # it's normally 1 or 0 for T and F, which bool() likes
            use = bool(int(camera[FIELDS["use"]].strip()))
        except ValueError:
            # if it isn't 1 or 0 (or any other int meaning true), then check if
            # it is any of the yes/true combiations below (case insensitive)
            use = camera[FIELDS["use"]].strip().lower() in ["t", "true", "y", "yes"]
        if use:
            yield camera

def find_image_files(camera, ext="jpg"):
    ext = ext.strip().strip(".")
    if ext.lower() in RAW_FORMATS:
        ext_dir = "raw"
    else:
        ext_dir = ext
    src = path.join(camera[FIELDS["source"]], ext_dir)
    walk = os.walk(src, topdown=True)
    for cur_dir, dirs, files in walk:
        if len(dirs) > 0:
            raise ValueError("too many subdirs")
        for fle in files:
            this_ext = path.splitext(fle)[-1].lower().strip(".")
            if this_ext == ext:
                fle_path = path.join(cur_dir, fle)
                yield fle_path


def generate_config_csv(filename):
    with open(filename, "w") as fh:
        fh.write(",".join([x for x in sorted(FIELDS.values())]))
        fh.write("\n")


def main(opts):
    if "-g" in opts:
        generate_config_csv(opts["-g"])
        exit()
    cameras = parse_camera_config_csv(opts["-c"])
    for camera in cameras:
        images = find_image_files(camera)
        process_camera_images(images)


if __name__ == "__main__":
    opts = docopt(CLI_OPTS)
    main(opts)
