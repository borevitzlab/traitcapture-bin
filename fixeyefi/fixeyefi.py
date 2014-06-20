from __future__ import print_function
import docopt
import csv
import glob
from os import path, makedirs
from shutil import copyfile, move
import sys

FILETYPES = {
    b'\xFF\xD8\xFF': "JPG",
    b'\x49\x49\x2A': "CR2",
}
FOLDER_NAMES = {
    "JPG": "JPG",
    "CR2": "RAW",
}

CLI_DOC = """
USAGE:
    fixeyefi.py [-m] -c CONFIG -i EYEFI_BASE

OPTIONS:
    -i EYEFI_BASE   Base directory of eyefi cache. Should contain MAC address
                    sub-folders.
    -c CONFIG       Config csv in format: MAC,Destination
    -m              Move files, don't copy
"""

def parse_config(opts):
    cameras = []
    with open(opts['-c']) as csvfh:
        csv_lines = csv.DictReader(csvfh)
        for line in csv_lines:
            try:
                mac = line["MAC"]
                dest = line["Destination"]
            except KeyError:
                print("ERROR: Malformed csv file. It should look like:\n")
                print("MAC,Destination\n18:03:73:3d:b7:56,/destination/dir")
                exit(1)
            camera =  {
                    "MAC": mac,
                    "Source": path.join(opts['-i'], mac),
                    "Destination": dest,
                    }
            cameras.append(camera)
    return cameras

def find_imgs(cam):
    imgs = glob.glob("{}/*".format(cam['Source']))
    for img in imgs:
        yield (path.basename(img), img)

def get_img_format(img):
    with open(img, "rb") as img_fh:
        magic = img_fh.read(3)
        try:
            return FILETYPES[magic]
        except KeyError:
            return None


def main(opts):
    cams = parse_config(opts)
    for cam in cams:
        count = 0
        copy = 0
        skip = 0
        print("Processing {}".format(cam["MAC"]))
        for name, img in find_imgs(cam):
            fmt = get_img_format(img)
            if not fmt:
                print("Skipping {}, not a JPG or TIFF".format(img))
                skip += 1
                count += 1
                continue
            dest = path.join(cam['Destination'], FOLDER_NAMES[fmt],
                "{}.{}".format(name, fmt))
            if path.exists(dest):
                skip += 1
                continue
            destdir = path.dirname(dest)
            if not path.exists(destdir):
                makedirs(destdir)
            if opts['-m']:
                move(img, dest)
            else:
                copyfile(img, dest)
            copy += 1
            if count % 10 == 0:
                print("Copied {: 5} images, skipped {: 5}".format(copy, skip),
                      end='\r')
                sys.stdout.flush()
            count += 1
        print("Processed {: 5} images. Done!                   ".format(count))

if __name__  == '__main__':
    opts = docopt.docopt(CLI_DOC)
    main(opts)
