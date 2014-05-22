#!/bin/bash

#####  GET OPTIONS #####
function help {
    echo -e "\n\n02-rotate.sh:\n"
    echo "USAGE:"
    echo -e "\t02-rotate.sh -i <infile> -o <outfile> (-c <camera> | -p <imagemagick params>)"
    exit 1
}

# Do getopts loop
while getopts :c:i:o:f: flag
do
    case $flag in
        c)
            cam="$OPTARG"
            ;;
        i)
            infile="$OPTARG"
            ;;
        o)
            outfile="$OPTARG"
            ;;
        p)
            param="$OPTARG"
            ;;
        *)
            echo "ERROR: bad argument $flag"
            help
            ;;
    esac
done

# Check options given
if [[ -z "$cam"  &&  -z "$param" ]]
then
    echo "ERROR: You must specify either a camera model, or a set of imagemagic -rotate parameters"
    help
fi

if [ -z "$infile" ]
then
    echo "ERROR: You must supply an input file"
    help
fi

if [ -z "$outfile" ]
then
    echo "ERROR: You must supply an output file"
    help
fi


# Get Fulla Params from camera model
if [ -n "$cam" ]
then
    case $cam in
        "StarDot5MP")
            param=""
            ;;
        "StarDot10MP")
            echo "WARNING, haven't tested this on the 10MP webcam images yet"
            param=""
            ;;
        "EOS18-55mm")
            param="-rotate -1.5"
            ;;
        *)
            echo "ERROR: Unsupported camera: $cam"
            echo "Supported Cameras are:"
            echo -e "\tStarDot5MP"
            echo -e "\tStarDot10MP"
            echo -e "\tEOS18-55mm"
            exit 1
            ;;
    esac
fi

if [ -n "${param}" ]
then
    convert "${params}"
fi
