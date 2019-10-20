#!/bin/bash

# This script uploads all files in a directory
# to Pokémon Central Wiki with given description,
# using filenames as they are, overwriting if
# told to and using given throttle

# Arguments:
#	- s: Source directory
#	- d: Description
#	- p: Flag, sets bot throttle to 1
#	- o: Flag, overwrite file if already exists, defaults to no

DIR=''
DESC=''
PT=''
OVERWRITE=false
EXISTSREACTION=abortonwarn

while getopts "s:d:po" OPTION; do
	case $OPTION in
		s)
			DIR="$OPTARG"
			;;
		d)
			DESC="$OPTARG"
			;;
		p)
			PT='-putthrottle:0'
			;;
		o)
			OVERWRITE=true
			;;
		*) # getopts already printed an error message
			exit 1
			;;
	esac
done

if [[ -z $DIR ]]; then
	echo No source directory specified. Aborting
	exit 1
fi
if [[ -z $DESC ]]; then
	echo No description given. Aborting
	exit 1
fi

if [[ $OVERWRITE == true ]]; then
	EXISTSREACTION=ignorewarn
fi

for FILE in "$DIR"/*; do
    python $PYWIKIBOT_DIR/pwb.py upload $PT -keep -noverify -$EXISTSREACTION:exists "$FILE" "$DESC"
done
