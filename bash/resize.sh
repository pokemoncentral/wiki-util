#!/bin/bash

# Ths script processes all images in a directory.
# The images are squared adding transparent pixels;
# the new size is the biggest one if it is greater
# than the provided one, else this very last

# Arguments
#	- $1: Directory images to be resized are in
#	- $2: Output size of images (default 150)
#	- o: Flag, unoptimizes gif

# Input processing
UNOPTIMIZE=false

while getopts "o" OPTION; do
	case $OPTION in
		o)
			UNOPTIMIZE=true
			;;
		*) # getopts already printed an error message
			exit 1
			;;
	esac
done

if [[ $@ =~ [[:space:]]- ]]; then
	echo "Error: option passed after parameters"
	exit 1
fi

shift $(( OPTIND - 1 ))

SOURCE_DIR="$1"
MIN_SIZE=${2:-150}

# Utility variables
OUT_DIR="$SOURCE_DIR"/Resized

mkdir -p "$OUT_DIR"

find "$SOURCE_DIR" -maxdepth 1 -type f -print0 | while IFS= read -r -d '' IMG; do
	IMG_TYPE=$(file -b "$IMG" | awk '{ print tolower($1) }')
	BASENAME=$(basename "$IMG")
	OUT_IMG="$OUT_DIR/$BASENAME"
	TARGET_FILE="$IMG"
	
	# Getting the biggest out of two sides and minumim size
	[[ $(identify "$IMG") =~ ([0-9]+)x([0-9]+) ]]
	if [[ ${BASH_REMATCH[1]} -gt ${BASH_REMATCH[2]} ]]; then
		SIZE=${BASH_REMATCH[1]}
	else
		SIZE=${BASH_REMATCH[2]}
	fi
	[[ $SIZE -lt $MIN_SIZE ]] && SIZE=$MIN_SIZE

	# Decompressing gifs
	if [[ $UNOPTIMIZE == true && $IMG_TYPE == 'gif' ]]; then
		echo "Unoptimizing gif..."
		TARGET_FILE="$SOURCE_DIR/__tmp.gif"
		gifsicle -U -o "$TARGET_FILE" "$IMG"
	fi

	# Actually resizing
	convert "$TARGET_FILE" -background transparent -gravity center -extent ${SIZE}x${SIZE} -quality 100 "$OUT_IMG"

	# Opimizing gifs
	if [[ $IMG_TYPE == 'gif' ]]; then
		if [[ $UNOPTIMIZE == true ]]; then
			rm "$TARGET_FILE"
		fi
		gifsicle -b -O3 "$OUT_IMG"
	fi

	echo "$BASENAME resized"
done
