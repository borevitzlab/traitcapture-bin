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


