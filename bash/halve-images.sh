#!/bin/bash

# This script undoes the effect of doubling the
# size on all images in an input directory, saving
# results in an output directory. This is useful,
# for instance, to halve upscaled MiniSprites

# This is done halving the size with a box filter
# (ie. the color of a pixel is the average of the
# four it correspond in the original image). This
# means using the same color if the original image
# is itself obtained extending each pixel to a 2x2
# square.

# Arguments:
#	- $1: Input directory
#	- $2: Output directory, created if not existing

INPUT_DIR="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

for FILE in "$INPUT_DIR"/*; do
	OUTFILE=$(basename "$FILE")
	OUTFILE="$OUTPUT_DIR/$OUTFILE"
	convert "$FILE" -filter box -resize 50% "$OUTFILE"
	echo Saved $FILE to $OUTFILE halving size
done
