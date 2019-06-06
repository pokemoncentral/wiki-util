#!/bin/bash

# Create a dict from a lua module.
# Can show differences with the page on the wiki
# and save it to a different location.

# Arguments:
#	- s: Source file
#	- d: Destination directory. Optional, if not given operates in place
#	- v: Flag, whether the script should show differences or not

SRC=''
DEST=''
DIFF=false

while getopts "s:d:v" OPTION; do
	case $OPTION in
		s)
			SRC="$OPTARG"
			;;
		d)
			DEST="$OPTARG"
			;;
		v)
			DIFF=true
			;;
		*) # getopts already printed an error message
			exit 1
			;;
	esac
done

if [[ -z $SRC ]]; then
	echo No source file specified. Aborting
	exit 1
fi
if [[ -z $DEST ]]; then
	echo No destination given. Operating in place
else
    cp $SRC $DEST
    SRC=$DEST/$(basename $SRC)
fi

node "$MACROS_DIR/run-macros.js" "$SRC" toModule
node "$MACROS_DIR/run-macros.js" "$SRC" moduleToDict

if [[ $DIFF == true ]]; then
    # Shows diff using pagefromfile. There may be a better script, but
    # this is just to have a working solution now

	yes | python $PYWIKIBOT_DIR/pwb.py pagefromfile -simulate -notitle -force -showdiff -pt:0 -file:"$SRC"
fi
