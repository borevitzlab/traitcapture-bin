#!/bin/bash

#####  GET OPTIONS #####
function help {
    echo -e "\n\nundistort-fulla.sh:\n"
    echo "USAGE:"
    echo -e "\tundistort-fulla.sh -i <infile> -o <outfile> (-c <camera> | -f <fulla params>)"
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
        f)
            FullaParm="$OPTARG"
            ;;
        *)
            echo "ERROR: bad argument $flag"
            help
            ;;
    esac
done

# Check options given
if [[ -z "$cam"  &&  -z "$FullaParam" ]]
then
    echo "ERROR: You must specify either a camera model, or a set of fulla parameters"
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
            FullaParam="-g 0:0:-0.11:1.11 -b 0:0:0.004:0.996"
            ;;
        "StarDot10MP")
            echo "WARNING, haven't tested this on the 10MP webcam images yet"
            FullaParam="-g 0:0:-0.11:1.11 -b 0:0:0.004:0.996"
            ;;
        "EOS18-55mm")
            FullaParam="-g 0:0:-0.02:1.02"
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

# Run fulla
fulla ${FullaParam} -o $outfile $infile
