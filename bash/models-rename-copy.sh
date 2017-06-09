#!/bin/bash

# This script renames all models in a
# directory, copying them to the provided
# destination path.

# Arguments
#	- $1: Source directory
#	- $2: Destination directory
#	- $3: Sprite variant. One of
#		- shiny
#		- back
#		- back_shiny
#		- normal
#	- $4: Sprite game. One of:
#		- xy
#		- oras
#		- roza
#		- sm
#		- sl

SOURCE="$1"
DEST="$2"
VARIANT="$3"
GAME="$4"

mkdir -p "$DEST"

for SPRITE in "$SOURCE"/*.gif; do
	SPRITE=$(basename $SPRITE)
    GENDER='m'

    [[ "$SPRITE" =~ .+-f\.gif ]] && GENDER='f'

    RENAMED=$(lua ../run.lua models-rename.lua $FILENAME $VARIANT $GENDER $GAME)
    DEST_SPRITE="$DEST"/"$RENAMED"

    if [[ -e "$DEST_SPRITE" ]]; then
        echo "$DEST_SPRITE from $SPRITE already exist" >> rename-move.log
    else
        cp "$SPRITE" "$DEST_SPRITE"
    fi
done
