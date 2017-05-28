#!/bin/bash

# This script gets the sizes of specified files
# and writes it to given output file in a format
# suitable to be parsed by sizeInfo Haskell program

# Arguments:
# 	- $1 files to be processed
# 	- $2 output file name

FILES="$1"
OUTFILE="$2"

:> $OUTFILE

for FILE in $FILES; do
	echo -n $(basename "$FILE") >> $OUTFILE
	[[ $(identify $FILE) =~ ([0-9]+)x([0-9]+) ]]
	echo -n " ${BASH_REMATCH[1]} " >> $OUTFILE
	echo ${BASH_REMATCH[2]} >> $OUTFILE
done
