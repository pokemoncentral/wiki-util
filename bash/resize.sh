#!/bin/bash

# Ths script processes all images in a directory.
# The images are squared adding transparent pixels;
# the new size is the biggest one if it is greater
# than the provided one, else this very last

# Arguments
#	- $1: Directory images to be resized are in
#	- $2: Output size of images (default 150)

# Input processing
SOURCE_DIR="$1"
MIN_SIZE=${2:-150}

# Utility variables
OUT_DIR="$SOURCE_DIR"/Resized

mkdir -p "$OUT_DIR"

for IMG in $(find "$SOURCE_DIR" -type f); do
	IMG_TYPE=$(file -b "$IMG" | awk '{ print tolower($1) }')
	BASENAME=$(basename "$IMG")
	OUT_IMG="$OUT_DIR/$BASENAME"
	
	# Getting the biggest out of two sides and minumim size
	[[ $(identify "$IMG") =~ ([0-9]+)x([0-9]+) ]]
	if [[ ${BASH_REMATCH[1]} -gt ${BASH_REMATCH[2]} ]]; then
		SIZE=${BASH_REMATCH[1]}
	else
		SIZE=${BASH_REMATCH[2]}
	fi
	[[ $SIZE -lt $MIN_SIZE ]] && SIZE=$MIN_SIZE

	# Optimized gifs yeld strange results, need to be unoptimized
	[[ $IMG_TYPE == 'gif' ]] && gifsicle --colors 256 -b --unoptimize "$IMG"

	# Actually resizing
	convert "$IMG" -background transparent -gravity center -extent ${SIZE}x${SIZE} -quality 100 "$OUT_IMG"

	# Optimizing gifs back
	[[ $IMG_TYPE == 'gif' ]] && gifsicle --colors 256 -b -O3 "$OUT_IMG"

	echo "$BASENAME resized"
done
