#!/bin/bash

# This script extracts the first frame out
# of all gif files in a directory and copies
# them to another path

# Arguments
#	- $1: the folder in which files are
#	- $2: the destination folder

SOURCE="$1"
DEST="$2"

mkdir -p "$DEST"

for FILE in "$SOURCE"/*; do
	if [[ $(bash file-type.sh "$FILE") == 'gif' ]]; then
		BASENAME=$(basename "$FILE")
		convert $FILE[0] "$DEST"/${BASENAME%.*}.png
	fi
done
