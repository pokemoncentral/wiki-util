#!/bin/bash

# This scripts trims transparent borders,
# then shrink any image in an input directory,
# saving the results, with the same name,
# in an output directory

# Arguments:
#	- $1: Input directory
#	- $2: Output directory, created if not existing
#	- $3: Maximum size, default to 1280

INPUT_DIR="$1"
OUTPUT_DIR="$2"
TMP_DIR="$INPUT_DIR/_tmp"
SIZE=${3:-1280}

mkdir -p "$OUTPUT_DIR"
mkdir -p $TMP_DIR

bash trim-images.sh "${INPUT_DIR}" $TMP_DIR

OIFS="$IFS"
IFS=$'\n'
for IMG in $(find $TMP_DIR -type f); do
	IMG_TYPE=$(bash file-type.sh "$IMG")
	BASENAME=$(basename "$IMG")
	OUTIMG="$OUTPUT_DIR/$BASENAME"

	convert "$IMG" -resize ${SIZE}x$SIZE\>  "$OUTIMG"

	echo "Saved shrinked $BASENAME to $OUTIMG" 
done

rm -rf $TMP_DIR
