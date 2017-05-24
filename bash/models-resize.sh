#!/bin/bash

# Arguments
# $1: The drectory in which source files are
# $2: Minimum size, defaults to 150px

# Input processing
SOURCE_DIR="$1"
MIN_SIZE=${2:-150}

# Utility variables
OUT_DIR="$SOURCE_DIR"/Resized

mkdir -p $OUT_DIR

for RAW_GIF in "$SOURCE_DIR"/*.gif; do
	[[ $(identify "$RAW_GIF") =~ ([0-9]+)x([0-9]+) ]]
	if [[ ${BASH_REMATCH[1]} -gt ${BASH_REMATCH[2]} ]]; then
		size=${BASH_REMATCH[1]}
	else
		size=${BASH_REMATCH[2]}
	fi
	if [[ $size -lt $MIN_SIZE ]]; then
		size=$MIN_SIZE
	fi

	NAME=$(basename "$RAW_GIF")
	OUT_GIF="$OUT_DIR"/$NAME

	convert $RAW_GIF -background transparent -gravity center -extent ${size}x${size} -format gif -quality 100 "$OUT_GIF"
	
	gifsicle -O3 --colors 256 --batch "$OUT_GIF"

	echo $NAME resized
done
