#!/bin/bash

# This scripts turns to transparent all the pixels
# outside the outline of all the pictures of an input
# directory, saving the result to a new png file with
# the same name in an output directory

# Arguments:
#	- $1: Input directory
#	- $2: Output directory, created if not existing

INPUT_DIR="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

for FILE in "$INPUT_DIR"/*; do
	OUTFILE=$(basename "$FILE")
	OUTFILE="$OUTPUT_DIR/${OUTFILE%.*}.gif"
	convert "$FILE" -fill transparent -fuzz 5% -draw 'color 0,0 floodfill' -morphology close diamond "$OUTFILE"
	echo Saved $FILE to $OUTFILE with transparent background
done
