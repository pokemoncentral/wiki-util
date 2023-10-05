#!/bin/bash

# Upload css files from wiki-styles repo

# Arguments:
#	- h: Show this help
#	- f: Flag, if set doesn't ask for confirmation

FORCE=false

while getopts "hf" OPTION; do
    case $OPTION in
        h)
            echo "Usage:
update-css [OPTIONS]... [PATH]

Upload css files from wiki-styles repo.
The argument is the path to the wiki-styles directory.

Arguments:
    - h: Show this help
    - f: Flag, if set doesn't ask for confirmation"
            exit 0
            ;;
		f)
			FORCE=true
			;;
		*) # getopts already printed an error message
			exit 1
			;;
	esac
done
shift $((OPTIND-1))

SRC="$1"

# Make a temp file to feed to pagefromfile
TMPFILE=$(mktemp -p .)
touch $TMPFILE
echo "{{-start-}}" >> $TMPFILE
echo "'''MediaWiki:Common.css'''" >> $TMPFILE
cat "$SRC/css/Common.css" >> $TMPFILE
echo "{{-stop-}}" >> $TMPFILE
echo "{{-start-}}" >> $TMPFILE
echo "'''MediaWiki:Mobile.css'''" >> $TMPFILE
cat "$SRC/css/Mobile.css" >> $TMPFILE
echo "{{-stop-}}" >> $TMPFILE

if [[ $FORCE == false ]]; then
    FLAGS="-showdiff"
fi

python $PYWIKIBOT_DIR/pwb.py pagefromfile -notitle -force -pt:0 -file:$TMPFILE -summary:"Updating styles (see wiki-styles repo)" $FLAGS

rm $TMPFILE
