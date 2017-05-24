#!/bin/bash

# This scripts trims transparent borders
# from all the images in an input directory,
# saving the results, with the same name,
# in an output directory

# Arguments:
#	- $1: Input directory
#	- $2: Output directory, created if not existing

INPUT_DIR="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

for IMG in "$INPUT_DIR"/*; do
	OUTIMG=$(basename "$IMG")
	EXT=${OUTIMG##*.}
	OUTIMG="$OUTPUT_DIR"/"$OUTIMG"

	case ${EXT,,} in
		'gif') # Gifs are handled using gifsicle
			gifsicle --crop-transparency "$IMG" > "$OUTIMG"

			# Don't know exactly why, but sometimes
			# the bottom-right corner only is trimmed:
			# rotating, trmming and rotating back
			# fixes this
			gifsicle --rotate-180 -b "$OUTIMG"
			gifsicle --crop-transparency -b "$OUTIMG"
			gifsicle --rotate-180 -b "$OUTIMG"
			;;

		*) # Any other format uses ImageMagick
			convert "$IMG" -trim +repage "$OUTIMG"
			;;
	esac

	echo Saved $IMG to $OUTIMG with transparent outer pixels removed 
done
