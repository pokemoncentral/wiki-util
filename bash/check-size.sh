#!/bin/bash

# Check that a list of files on PCW have the
# right size (in pixel)
#
# Requires the custom script imagedownload to work

TMPDIR=/tmp/check-size-tmp

while getopts "h" OPTION; do
	case $OPTION in
		h)
			echo "This script checks that a list of files on PCW have the
right size (in pixel)

The first argument is the list of files, one name per line
(without \"File:\" prefix)

Arguments:
	- h: Show this help"
			exit 0
			;;
		*) # getopts already printed an error message
			exit 1
			;;
	esac
done
shift $(( $OPTIND - 1 ))

LIST="$1"
OUTLIST="$1-checked"

mkdir -p "$TMPDIR"
chmod 777 "$TMPDIR"
touch "$OUTLIST"

while read filename; do
    DWLNAME="File:$filename"
    python $PYWIKIBOT_DIR/pwb.py imagedownload -target:"$TMPDIR" "$DWLNAME" &> /dev/null

    if [[ -f "$TMPDIR/$filename" ]]; then
        FILESIZE=$(identify "$TMPDIR/$filename" | head -n1 | cut -d' ' -f3)
        if [[ $FILESIZE == 150x150 ]]; then
            echo "$filename is 150x150"
        else
            echo "$filename is ${FILESIZE}: adding to the list"
	        echo "$filename" >> $OUTLIST
        fi
    else
        echo "$filename doesn't exists on the target Wiki. Skipping"
    fi
done < $LIST

rm -rf "$TMPDIR"
