#!/bin/bash

if [ $# -ne 3 ]
then
	echo "HAFResize.sh -- The hacky-as-fuck timestream resizer"
	echo
	echo "USAGE:"
	echo "	hafresize.sh <timestream> <x> <y>"
	echo "OPTIONS:"
	echo "	<timestream>	Path to timestream to be resized."
	echo "	<x>		X coordinate to resize to."
	echo "	<y>		Y coordinate to resize to. If -1, it is calculated from the first image's aspect ratio."
	exit
fi

ts="${1}"

if [ $3 -gt 0 ]
then
	newres="${2}x${3}"
else
	newres="$2"
fi

if [ ! -d $ts ]
then
	echo "ERROR: timestream must exist" >&2
	exit -1
fi

new_ts=$(echo $ts |  sed -e "s/fullres/$newres/g")
if [ -d "$new_ts" ]
then
	echo "ERROR: new timestream already exists" >&2
	exit -1
fi

echo "resizing $ts to $newres"
dirs=$(find $ts -type d -print | sed -e "s/fullres/$newres/g")
echo "$dirs" | parallel mkdir -p

find $ts -name \*.jpg -or -name \*.JPG | \
       	parallel convert -resize $newres {} \"\$\(echo \'{}\' \| sed \'s/fullres/$newres/g\' \| sed \'s/\\\\//g\'  \)\" \; echo -n \'.\'

