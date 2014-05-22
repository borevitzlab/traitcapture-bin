#!/bin/bash

scriptDir="$(dirname $(readlink -f $0))"
source "${scriptDir}/util.sh"

#####  GET OPTIONS #####
function help {
    echo -e "\ntimelapse.sh:\n"
    echo "USAGE:"
    echo -e "\ttimelapse.sh -n <camera_name> -p <destination path> [ -c <camera> ] [ -i <interval> ] [ -f <filename pattern> ]"
    echo
    echo "OPTIONS:"
    echo -e "\t-c\tThe camera port, use gphoto --auto-detect to determine the correct value. By default, the --port option will not be passed to gphoto2."
    echo -e "\t-i\tCapture interval in seconds. DEFAULT = 10."
    echo -e "\t-f\tFilename date format given to gphoto2. DEFAULT = %y%m%d_%H%M%S, giving a filename e.g. <camname>_20130502_135302_<photoNum>.jpeg"
    echo -e "\t-p\tPath to base of image destination folders. Must be provided. e.g. ~/images/"
    echo -e "\t-n\tNickname for this camera. Must be provided."
    exit 1
}

# Do getopts loop
while getopts :p:n:f:c:i: flag
do
    case $flag in
        n)
            camName="$OPTARG"
            ;;
        f)
            filename="$OPTARG"
            ;;
        p)
            path="$OPTARG"
            ;;
        c)
            cameraPort="$OPTARG"
            ;;
        i)
            interval="$OPTARG"
            ;;
        *)
            echo "ERROR: bad argument $flag"
            help
            ;;
    esac
done

if [ -z "$path" ]
then
    echo "ERROR: Destination path must be provided"
    help
fi

if [ -z "$camName" ]
then
    echo "ERROR: Nickname for camera must be provided"
fi

if [ -z "$interval" ]
then
    interval=10
fi

if [ -z "$filename" ]
then
    filename="%y%m%d_%H%M%S"
fi

# Prepare arguments
destinationPath="${path}/${camName}"
if [ -n "$cameraPort" ]
then
    portArg="--port=${cameraPort}"
    echo $cameraPort ${portArg}
fi

# Run gphoto
if [ ! -d "$destinationPath" ]
then
    mkdir -p "$destinationPath"
fi


numPhotos=0
while true
do
	getNow
	numPhotos=$((numPhotos + 1))
	thisFilename="${destinationPath}/${camName}_${filename}_${numPhotos}.jpeg"
	echo "Capturing photo # ${numPhotos} to file ${thisFilename}"

	tmpfile="/tmp/eyepi_timelapse_$RANDOM"
	echo gphoto2 --force-overwrite --filename ${thisFilename} ${portArg} --capture-image-and-download
	gphoto2 --force-overwrite --filename ${thisFilename} ${portArg} --capture-image-and-download  2>&1 | tee $tmpfile
	res=$?
	if [ $res -ne 0 ]
	then
		cat $tmpfile
		#TODO: email log
	fi

	secTimer
	sleepLen=$(($interval - $TIMER_SECS))
	if [ $sleepLen -lt 0 ]
	then
		sleepLen=0
	fi
	sleep $sleepLen
	rm -f $tmpfile
done
