import exifread as er
from time import strptime, strftime
from csv import reader, DictReader
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import os
import shutil
from PIL import Image
import time



EXIF_DATE_TAG = "Image DateTime"
EXIF_DATE_FMT = "%Y:%m:%d %H:%M:%S"

TS_V1_FMT = ("%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/"
             "{tsname:s}~%Y_%m_%d_%H_%M_%S_{n:02d}.{ext:s}")
TS_V2_FMT = ("%Y/%Y_%m/%Y_%m_%d/%Y_%m_%d_%H/"
             "{tsname:s}~%Y_%m_%d_%H_%M_%S_{n:02d}.{ext:s}")
TS_FMT = TS_V1_FMT


def get_file_date(filename):
    """Gets a time.struct_time from an image's EXIF, or None if not possible"""
    with open(filename, "rb") as fh:
        exif_tags = er.process_file(fh, details=False, stop_tag=EXIF_DATE_TAG)
    try:
        str_date = exif_tags[EXIF_DATE_TAG].values
        date = strptime(str_date, EXIF_DATE_FMT)
    except KeyError:
        date = None
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
    im = Image.open(src_fn)
    if keep_aspect:
        im.thumbnail((x, y), Image.ANTIALIAS)
    else:
        if crop:
            pass
        else:
            im = im.resize((x, y), Image.ANTIALIAS)
    im.save(dest_fn, fmt)
    return im


def round_struct_time(in_time, round_secs, tz_hrs=0, uselocal=True):
    """
    Round a struct_time object to any time lapse in seconds
    """
    seconds = time.mktime(in_time)
    rounded = int(round(seconds / float(round_secs)) * round_secs)
    if not uselocal:
        rounded -= tz_hrs * 60 * 60 # remove tz seconds, back to UTC
    return time.localtime(rounded)
