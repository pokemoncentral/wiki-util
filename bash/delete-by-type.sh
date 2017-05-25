#!/bin/bash

# This script deletes files if they are
# not of one of the specified types,
# regardeless of the actual file name
# extension.

# If a directory is passed, all files in
# it not satisfying this criterion are
# deleted; when a file is given, it is
# checked and possibly deleted instead.

# Arguments:
#	- $1: Path to delete from: if it is
#		a directory, files in it are deleted,
#		otherwise the file itself is.
#	- $2+: Accepted file types

# Removes the passed file if not in the
# accepted file types
delIfNot () {
    local FILE="$1"
    shift 1
    local ACCEPTED_TYPES="$*"

	local FILE=$(echo "$FILE" | uni2ascii -aJ)
    local ACCEPTED_TYPES=${ACCEPTED_TYPES,,}

    local FILE_TYPE=$(file -b "$FILE" | awk '{ print tolower($1) }')

    [[ ! $ACCEPTED_TYPES =~ $FILE_TYPE ]] && rm "$FILE"
}

FILE_PATH="$1"
shift 1
TYPES="$@"

if [[ -d "$FILE_PATH" ]]; then
	for FILE in "$FILE_PATH"/*; do
		delIfNot "$FILE" $TYPES
	done
else
	delIfNot "$FILE_PATH" $TYPES
fi
