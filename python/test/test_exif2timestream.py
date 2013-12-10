import unittest
import os
from os import path
import exif2timestream as e2t
import time
from shutil import rmtree
from hashlib import md5

class TestExifTraitcapture(unittest.TestCase):
    dirname = path.dirname(__file__)
    out_dirname = path.join(dirname, "out")

    jpg_testfile = path.join(dirname, "img", "IMG_0001.JPG")
    raw_testfile = path.join(dirname, "img", "IMG_0001.CR2")

    # helpers
    def _md5test(self, filename, expected_hash):
        with open(filename, "rb") as fh:
            out_contents = fh.read()
        md5hash = md5()
        md5hash.update(out_contents)
        md5hash = md5hash.hexdigest()
        self.assertEqual(md5hash, expected_hash)

    # setup
    def setUp(self):
        os.mkdir(self.out_dirname)

    # tests for round_struct_time
    def test_round_struct_time_gmt(self):
        start = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        rnd_5 = e2t.round_struct_time(start, 300, tz_hrs=11, uselocal=False)
        rnd_5_expt = time.strptime("20131112 095500", "%Y%m%d %H%M%S")
        self.assertIsInstance(rnd_5, time.struct_time)
        self.assertEqual(time.mktime(rnd_5), time.mktime(rnd_5_expt))

    def test_round_struct_time_local(self):
        start = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        rnd_5 = e2t.round_struct_time(start, 300, tz_hrs=11)
        rnd_5_expt = time.strptime("20131112 205500", "%Y%m%d %H%M%S")
        self.assertIsInstance(rnd_5, time.struct_time)
        self.assertEqual(time.mktime(rnd_5), time.mktime(rnd_5_expt))

    def test_get_file_date_jpg(self):
        actual = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        jpg_date = e2t.get_file_date(self.jpg_testfile)
        self.assertEqual(jpg_date, actual)

    def test_get_file_date_raw(self):
        actual = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        raw_date = e2t.get_file_date(self.raw_testfile)
        self.assertEqual(raw_date, actual)

    def test_resize_image_keepaspect(self):
        out = path.join(self.out_dirname, "im1_thumbed_640x480.jpg")
        im = e2t.resize_image(out, self.jpg_testfile, 640, 480,
                keep_aspect=True)
        self._md5test(out, "967e7f01b1c42d693c42c201dddc0e6c")

    def test_resize_image(self):
        out = path.join(self.out_dirname, "im1_resized_640x480.jpg")
        im = e2t.resize_image(out, self.jpg_testfile, 640, 480)
        self._md5test(out, "713af12ccbcf79ec1af5651f0d42e23d")

    def tearDown(self):
        rmtree(self.out_dirname)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    unittest.main(testRunner=runner)
