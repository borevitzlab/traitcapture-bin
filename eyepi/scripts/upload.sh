#!/bin/bash

# Rsync:
#DefaultCpProgOpts="-rviht --progress"

# scp:
DefaultCpProgOpts=""

#####  GET OPTIONS #####
function help {
    echo -e "\nupload.sh:\n"
    echo "USAGE:"
    echo -e "\tupload.sh -n <camera_name> -p <source path>  -P <destination path> -r <cpprog_args>"
    echo
    echo "OPTIONS:"
    echo -e "\t-p\tPath to base of image destination folders. Must be provided. e.g. ~/images/. Same as given to timelapse.sh"
    echo -e "\t-n\tNickname for this camera. Must be provided."
    echo -e "\t-P\tRsync Destination Path. Must be provided."
    exit 1
}

# Do getopts loop
while getopts :p:P:n:r: flag
do
    case $flag in
        n)
            name="$OPTARG"
            ;;
        p)
            srcpath="$OPTARG"
            ;;
        P)
            destpath="$OPTARG"
            ;;
        r)
            cpprogargs="$OPTARG"
            ;;
        ?)
            echo "ERROR: bad argument $OPTARG"
            help
            ;;
    esac
done

if [ -z "$srcpath" ]
then
    echo "ERROR: Source path must be provided"
    help
fi

if [ -z "$destpath" ]
then
    echo "ERROR: Destination path must be provided"
    help
fi

if [ -z "$name" ]
then
    echo "ERROR: Nickname for camera must be provided"
fi

if [ -z "$cpprogargs" ]
then
	cpprogargs="${DefaultCpProgOpts}"
fi


# don't rsync, phenocam.anu.edu.au is a windoze box
#rsync
set -x
scp "$cpprogargs" "$srcpath" "$destpath"
set +x
