#!/bin/bash

ts="${1}"
newres="${2}x${3}"
echo "resizing $ts to $newres"

new_ts=$(echo $ts |  sed -e "s/fullres/$newres/g")
if [ -d "$new_ts" ]
then
	echo "new timestream already exists"
	exit
fi

dirs=$(find $ts -type d -print | sed -e "s/fullres/$newres/g")
echo "$dirs" | parallel mkdir -p

find $ts -name \*.jpg -or -name \*.JPG | \
       	parallel convert -resize $newres {} \"\$\(echo \'{}\' \| sed \'s/fullres/$newres/g\' \| sed \'s/\\\\//g\'  \)\" \; echo -n \'.\'

