#!/bin/bash

# This script downloads a list of files
# contained in a file by means of
# get-wiki-file.sh.

# Arguments:
#   - $1: Files list file (format described below)
#   - $2: Destination directory
#   - $3+: arguments passed to get-wiki-file.sh
#       (named included)

# Input format is source filename first
# and destination on the following line:
# if the file name is the same, only the
# destination is necessary. This is why
# destination lines should be marked by
# prefixing them with the following $DEST_TAG.

# Example
#   773Silvally_Acciaio_Dream.png
#   # 773Silvally_Steel_Dream.png
#   773Silvally_Erba_Dream.png
#   # 773Silvally_Grass_Dream.png
#   # 050Diglett_Alola_Dream.png
#   773Silvally_Elettro_Dream.png
#   # 773Silvally_Electric_Dream.png

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

    # Only destiantion found
    [[ -z $SOURCE ]] && SOURCE=$DEST

    # Dest is also empty, something went wrong
    if [[ -z $SOURCE ]]; then
        echo 'Malformed input'
        exit 1
    fi
    
	IFS=$OLD_IFS

    bash get-wiki-file.sh $@ "$SOURCE" "$DEST_DIR/$DEST"

    OLD_IFS=$IFS
	IFS='\n'

    SOURCE=''
    DEST=''

done < "$PAIRS"
