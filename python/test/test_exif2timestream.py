from copy import deepcopy
import exif2timestream as e2t
from hashlib import md5
import os
from os import path
from shutil import rmtree, copytree
import time
from time import strptime
import unittest
from voluptuous import MultipleInvalid

class TestExifTraitcapture(unittest.TestCase):
    dirname = path.dirname(__file__)
    test_config_csv = path.join(dirname, "test_config.csv")
    bad_header_config_csv = path.join(dirname, "bad_header_config.csv")
    bad_values_config_csv = path.join(dirname, "bad_values_config.csv")
    out_dirname = path.join(dirname, "out")
    camupload_dir = path.join(dirname, "img", "camupload")
    noexif_testfile = path.join(dirname, "img", "IMG_0001_NOEXIF.JPG")
    jpg_testfile = path.join(camupload_dir, "jpg", "IMG_0001.JPG")
    raw_testfile = path.join(camupload_dir, "raw", "IMG_0001.CR2")
    camera_win32 = {
            'archive_dest': '/'.join([out_dirname, 'archive']),
            'current_expt': 'BVZ00000',
            'destination': '\\'.join([out_dirname, 'timestreams']),
            'expt_end': '2013_12_31',
            'expt_start': '2013_11_01',
            'location': 'EUC-R01C01',
            'method': 'copy',
            'image_types': 'raw~jpg',
            'interval': '5',
            'mode': 'batch',
            'camera_name_f': 'IP01-RGB',
            'resolutions': 'original~1024x768~640x480',
            'source': '\\'.join([dirname, "img", "camupload"]),
            'sunrise': '500',
            'sunset': '2200',
            'camera_timezone': '1100',
            'use': '1',
            'user': 'Glasshouses'
            }
    camera_unix = {
            'archive_dest': '/'.join([out_dirname, 'archive']),
            'current_expt': 'BVZ00000',
            'destination': '/'.join([out_dirname, 'timestreams']),
            'expt_end': '2013_12_31',
            'expt_start': '2013_11_01',
            'location': 'EUC-R01C01',
            'method': 'copy',
            'interval': '5',
            'image_types': 'raw~jpg',
            'mode': 'batch',
            'camera_name_f': 'IP01-RGB',
            'resolutions': 'original~1024x768~640x480',
            'source': '/'.join([dirname, "img", "camupload"]),
            'sunrise': '500',
            'sunset': '2200',
            'camera_timezone': '1100',
            'use': '1',
            'user': 'Glasshouses'
            }

    r_fullres_path =  path.join(
        out_dirname, "timestreams",
        'BVZ00000-EUC-R01C01-IP01-RGB~fullres-orig', '2013', '2013_11',
        '2013_11_12', '2013_11_12_20',
        'BVZ00000-EUC-R01C01-IP01-RGB~fullres-orig_2013_11_12_20_55_00_00.JPG'
        )
    r_1080_path =  path.join(
        out_dirname, "timestreams",
        'BVZ00000-EUC-R01C01-IP01-RGB~1024x768-orig', '2013', '2013_11',
        '2013_11_12', '2013_11_12_20',
        'BVZ00000-EUC-R01C01-IP01-RGB~1024x768-orig_2013_11_12_20_55_00_00.JPG',
        )
    r_640_path =  path.join(
        out_dirname, "timestreams",
        'BVZ00000-EUC-R01C01-IP01-RGB~640x480-orig', '2013', '2013_11',
        '2013_11_12', '2013_11_12_20',
        'BVZ00000-EUC-R01C01-IP01-RGB~640x480-orig_2013_11_12_20_55_00_00.JPG'
        )

    maxDiff = None

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
        if path.sep == "/":
            self.camera_raw = deepcopy(self.camera_unix)
            self.camera = deepcopy(self.camera_unix)
        else:
            self.camera_raw = deepcopy(self.camera_win32)
            self.camera = deepcopy(self.camera_win32)
        img_dir = path.dirname(self.camera[e2t.FIELDS['source']])
        if not path.exists(img_dir):
            os.mkdir(img_dir)
        if not path.exists(self.out_dirname):
            os.mkdir(self.out_dirname)
        if not path.exists(self.camera[e2t.FIELDS['destination']]):
            os.mkdir(self.camera[e2t.FIELDS['destination']])
        if not path.exists(self.camera[e2t.FIELDS['archive_dest']]):
            os.mkdir(self.camera[e2t.FIELDS['archive_dest']])
        rmtree(img_dir)
        copytree("./test/unburnable", img_dir)
        self.camera = e2t.validate_camera(self.camera)

    # test for localise_cam_config
    def test_localise_cam_config(self):
        self.assertDictEqual(
                e2t.localise_cam_config(self.camera_win32),
                self.camera_raw)
        self.assertDictEqual(
                e2t.localise_cam_config(self.camera_unix),
                self.camera_raw)

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

    # tests for get_file_date
    def test_get_file_date_jpg(self):
        actual = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        jpg_date = e2t.get_file_date(self.jpg_testfile)
        self.assertEqual(jpg_date, actual)

    def test_get_file_date_raw(self):
        actual = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        raw_date = e2t.get_file_date(self.raw_testfile)
        self.assertEqual(raw_date, actual)

    def test_get_file_date_noexif(self):
        date = e2t.get_file_date(self.noexif_testfile)
        self.assertIsNone(date)

    # tests for resize_image
    def test_resize_image_keepaspect(self):
        out = path.join(self.out_dirname, "im1_thumbed_640x480.jpg")
        im = e2t.resize_image(out, self.jpg_testfile, 640, 480,
                keep_aspect=True)
        self._md5test(out, "967e7f01b1c42d693c42c201dddc0e6c")

    def test_resize_image(self):
        out = path.join(self.out_dirname, "im1_resized_640x480.jpg")
        im = e2t.resize_image(out, self.jpg_testfile, 640, 480)
        self._md5test(out, "713af12ccbcf79ec1af5651f0d42e23d")

    def test_resize_image_crop(self):
        out = path.join(self.out_dirname, "im1_resized_640x480.jpg")
        with self.assertRaises(NotImplementedError):
            e2t.resize_image(out, self.jpg_testfile, 640, 480,
                keep_aspect=False, crop=True)

    # tests for get_new_file_name
    def test_get_new_file_name(self):
        date = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        fn = e2t.get_new_file_name(date, 'test')
        self.assertEqual(fn, ("2013/2013_11/2013_11_12/2013_11_12_20/"
                              "test_2013_11_12_20_53_09_00.jpg"))

    def test_get_new_file_date_from_file(self):
        date = e2t.get_file_date(self.jpg_testfile)
        fn = e2t.get_new_file_name(date, 'test')
        self.assertEqual(fn, ("2013/2013_11/2013_11_12/2013_11_12_20/"
                              "test_2013_11_12_20_53_09_00.jpg"))
        date = e2t.get_file_date(self.jpg_testfile, round_secs=5*60)
        fn = e2t.get_new_file_name(date, 'test')
        self.assertEqual(fn, ("2013/2013_11/2013_11_12/2013_11_12_20/"
                              "test_2013_11_12_20_55_00_00.jpg"))

    def test_get_new_file_nulls(self):
        date = time.strptime("20131112 205309", "%Y%m%d %H%M%S")
        with self.assertRaises(ValueError):
            e2t.get_new_file_name(None, 'test')
        with self.assertRaises(ValueError):
            e2t.get_new_file_name(date, '')
        with self.assertRaises(ValueError):
            e2t.get_new_file_name(date, None)
        with self.assertRaises(ValueError):
            e2t.get_new_file_name(None, '')

    # tests for make_timestream_name
    def test_make_timestream_name_empty(self):
        name = e2t.make_timestream_name(self.camera)
        exp = 'BVZ00000-EUC-R01C01-IP01-RGB~fullres-orig'
        self.assertEqual(name, exp)

    def test_make_timestream_name_params(self):
        name = e2t.make_timestream_name(
                self.camera,
                res="1080x720",
                step="clean")
        exp = 'BVZ00000-EUC-R01C01-IP01-RGB~1080x720-clean'
        self.assertEqual(name, exp)

    # tests for find_image_files
    def test_find_image_files(self):
        expt = {"jpg": {path.join(self.camupload_dir, x) for x in [
                        'jpg/IMG_0001.JPG',
                        'jpg/IMG_0630.JPG',
                        'jpg/IMG_0633.JPG']
                        },
                "raw": {path.join(self.camupload_dir, 'raw/IMG_0001.CR2')},
            }
        got = e2t.find_image_files(self.camera)
        self.assertSetEqual(set(got["jpg"]), expt["jpg"])
        self.assertSetEqual(set(got["jpg"]), expt["jpg"])

    def test_get_local_path(self):
        winpath = "test\\path\\to\\file"
        unixpath = "test/path/to/file"
        if os.path.sep == "\\":
            # windows
            self.assertEqual(e2t.get_local_path(winpath), winpath)
            self.assertEqual(e2t.get_local_path(unixpath), winpath)
        elif os.path.sep == "/":
            # unix
            self.assertEqual(e2t.get_local_path(winpath), unixpath)
            self.assertEqual(e2t.get_local_path(unixpath), unixpath)
        else:
            raise ValueError("Non-Unix/Win path seperator '%s' not supported" %
                    os.path.sep)

    # tests for do_image_resizing
    def test_do_image_resizing(self):
        e2t.do_image_resizing(self.jpg_testfile, self.camera)
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")

    def test_do_image_resizing_params(self):
        # with keep-aspect = T
        e2t.do_image_resizing(self.jpg_testfile, self.camera, keep_aspect=True)
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "be834a62e71373f2103426d07457beb0")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "967e7f01b1c42d693c42c201dddc0e6c")
        # with keep-aspect = F, crop = T
        # NOT IMPLEMENTED, HENCE COMMENTED
        #e2t.do_image_resizing(self.jpg_testfile, self.camera, crop=True)
        #self.assertTrue(path.exists(self.r_1080_path))
        #self._md5test(self.r_1080_path, "")
        #self.assertTrue(path.exists(self.r_640_path))
        #self._md5test(self.r_640_path, "")

    # tests for timestreamise_image
    def test_timestreamise_image(self):
        e2t.timestreamise_image(self.jpg_testfile, self.camera)
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")


    # tests for process_image
    def test_process_image(self):
        e2t.process_image((self.jpg_testfile, self.camera, "jpg"))
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")

    def test_process_image_map(self):
        map(e2t.process_image, [(self.jpg_testfile, self.camera, "jpg")])
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")

    # tests for parse_camera_config_csv
    def test_parse_camera_config_csv(self):
        configs = [
                {
                    'archive_dest': './test/out/archive',
                    'camera_name_f': 'IP01-RGB',
                    'camera_timezone': (11,0),
                    'current_expt': 'BVZ00000',
                    'destination': './test/out/timestreams',
                    'expt_end': strptime('2013_12_31', "%Y_%m_%d"),
                    'expt_start': strptime('2013_12_01', "%Y_%m_%d"),
                    'interval': 5,
                    'image_types': ["jpg"],
                    'location': 'EUC-R01C01',
                    'method': 'move',
                    'mode': 'batch',
                    'resolutions': ['original', (1024,768), (640,480)],
                    'source': './test/img/camupload',
                    'sunrise': (5,0),
                    'sunset': (22,0),
                    'use': True,
                    'user': 'Glasshouses'
                }
            ]
        result = e2t.parse_camera_config_csv(self.test_config_csv)
        for expt, got in zip(configs, result):
            self.assertDictEqual(got, expt)

    def test_parse_camera_config_csv_badconfig(self):
        with self.assertRaises(KeyError):
            list(e2t.parse_camera_config_csv(self.bad_header_config_csv))
        with self.assertRaises(MultipleInvalid):
            list(e2t.parse_camera_config_csv(self.bad_values_config_csv))

    # tests for generate_config_csv
    def test_generate_config_csv(self):
        out_csv = path.join(self.out_dirname, "test_gencnf.csv")
        e2t.generate_config_csv(out_csv)
        self._md5test(out_csv, "de1cd9eb7d630c38bf1ece0237004b1b")

    # tests for main function
    def test_main(self):
        e2t.main({
            '-1': False,
            '-a': None,
            '-c': './test/test_config.csv',
            '-g': None,
            '-t': None})
        #os.system("tree %s" % path.dirname(self.out_dirname))
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")

    def test_main_threads(self):
        # with a good value for threads
        e2t.main({
            '-1': False,
            '-a': None,
            '-c': './test/test_config.csv',
            '-g': None,
            '-t': '2'})
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")

    def test_main_threads_bad(self):
        # and with a bad one (should default back to n_cpus)
        e2t.main({
            '-1': False,
            '-a': None,
            '-c': './test/test_config.csv',
            '-g': None,
            '-t': "several"})
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")

    def test_main_threads_one(self):
        # and with -1
        e2t.main({
            '-1': True,
            '-a': None,
            '-c': './test/test_config.csv',
            '-g': None,
            '-t': None})
        self.assertTrue(path.exists(self.r_fullres_path))
        self._md5test(self.r_fullres_path, "76ee6fb2f5122d2f5815101ec66e7cb8")
        self.assertTrue(path.exists(self.r_1080_path))
        self._md5test(self.r_1080_path, "77998432afa84187aeb4e9a5f904a4df")
        self.assertTrue(path.exists(self.r_640_path))
        self._md5test(self.r_640_path, "713af12ccbcf79ec1af5651f0d42e23d")


    def test_main_generate(self):
        conf_out = path.join(self.out_dirname, "config.csv")
        with self.assertRaises(SystemExit):
            e2t.main({
                '-1': False,
                '-a': None,
                '-c': None,
                '-g': conf_out,
                '-t': None})
        self.assertTrue(path.exists(conf_out))
        self._md5test(conf_out, "de1cd9eb7d630c38bf1ece0237004b1b")

    def tearDown(self):
        #os.system("tree %s" % path.dirname(self.out_dirname))
        rmtree(self.out_dirname)
        #pass


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    unittest.main(testRunner=runner)
