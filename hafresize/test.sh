#!/bin/bash

set -e
set -x

function assertSizes() {
	timestream="$1"
	expected="$2"

	pushd $timestream
	for size in $(find -name \*.jpg -or -name \*.JPG | parallel identify -format "%[fx:w]x%[fx:h]")
	do
		if [ "$size" != "$expected" ] ; then exit -1; fi
	done
	popd
}


# test resize to 1920x1280 (giving both parameters)

time bash ./hafresize.sh 'test/BVZ0022-GC05L-CN650D-Cam07~fullres-orig' 1920 1280
if [ ! -d 'test/BVZ0022-GC05L-CN650D-Cam07~1920x1280-orig' ]
then
       	echo "failed to create timestream at 'test/BVZ0022-GC05L-CN650D-Cam07~1920x1280-orig'"; exit -1;
fi
assertSizes "test/BVZ0022-GC05L-CN650D-Cam07~1920x1280-orig" '1920x1280'
rm -r "test/BVZ0022-GC05L-CN650D-Cam07~1920x1280-orig"

# test resize to 1920x1280 (giving only x parameter)

time bash ./hafresize.sh 'test/BVZ0022-GC05L-CN650D-Cam07~fullres-orig' 1920 -1
if [ ! -d 'test/BVZ0022-GC05L-CN650D-Cam07~1920-orig' ]
then
       	echo "failed to create timestream at 'test/BVZ0022-GC05L-CN650D-Cam07~1920-orig'"; exit -1;
fi
assertSizes "test/BVZ0022-GC05L-CN650D-Cam07~1920-orig" '1920x1280'
rm -r "test/BVZ0022-GC05L-CN650D-Cam07~1920-orig"

# all done, clean up
echo "all tests passed"
