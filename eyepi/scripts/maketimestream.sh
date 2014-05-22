#!/bin/bash


#####  GET OPTIONS #####
function help {
    echo -e "\nmaketimestream.sh:\n"
    echo "USAGE:"
    echo -e "\tmaketimestream.sh -n <camera_name> -P <source path> -p <destination path> -t <timestream_name>"
    echo
    echo "OPTIONS:"
    echo -e "\t-P\tPath to base of eyepi image destination folders. Must be provided. e.g. ~/images/"
    echo -e "\t-p\tPath to base of timestream folders. Must be provided. e.g. ~/timestreams/"
    echo -e "\t-n\tNickname for this camera. Must be provided."
    exit 1
}

# Do getopts loop
while getopts :p:n:f:i: flag
do
    case $flag in
        n)
            name="$OPTARG"
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

if [ -z "$name" ]
then
    echo "ERROR: Nickname for camera must be provided"
fi

if [ -z "$interval" ]
then
    interval=10
fi

if [ -z "$filename" ]
then
    filename="%y%m%d_%H%M%S.jpeg"
fi


