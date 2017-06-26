#!/bin/bash

DEST_TAG='# '

PAIRS="$1"
DEST_DIR="$2"
shift 2

mkdir -p "$DEST_DIR"

OLD_IFS=$IFS
IFS='\n'

SOURCE=''
DEST=''

while read -r FILENAME; do
    if [[ ${FILENAME:0:2} = $DEST_TAG ]]; then
        DEST=${FILENAME:2}
    else
        SOURCE=$FILENAME
        continue
    fi

    [[ -z $SOURCE ]] && SOURCE=$DEST
    [[ -z $SOURCE ]] && { echo 'Malformed input'; exit 1; }
    
	IFS=$OLD_IFS

    bash get-wiki-file.sh $@ "$SOURCE" "$DEST_DIR/$DEST"

    OLD_IFS=$IFS
	IFS='\n'

    SOURCE=''
    DEST=''

done < "$PAIRS"
