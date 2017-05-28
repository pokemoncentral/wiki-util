#!/bin/bash

# Arguments
# $1: source folder
# $2: dest folder
# $3: variant [shiny, back, back_shiny, normal]
# $4: game [xy, oras, roza]

SOURCE="$1"
DEST="$2"

mkdir -p "$DEST"

for FILE in "$SOURCE"/*.gif; do
    GENDER='m'
	FILENAME=$(basename $FILE)

    [[ $FILENAME =~ .+-f\.gif ]] && GENDER='f'

    RENAMED=$(bash models-rename.sh $FILENAME $3 $GENDER $4)
    DEST_FILE="$DEST"/"$RENAMED"

    if [[ -e "$DEST_FILE" ]]; then
        echo "$DEST_FILE from $FILENAME already exist" >> rename-move.log
    else
        cp "$FILE" "$DEST_FILE"
    fi
done
