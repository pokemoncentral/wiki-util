#!/bin/bash

# This script downloads files having
# sequential names.

# It doesn't use command line arguments
# for the range, though, because the
# super powers of bash .. built-in only
# work with literals

# All the arguments from the third onwards
# are directly passed to getWikiFile.sh,
# including named parameters and flags

# Arguments
#	- $1: Sequence number prefix
#	- $2: Sequence number suffix
#	- $3: Destination path
#	- $4+: getWikiFile.sh parameters

PREFIX="$1"
SUFFIX="$2"
DEST="$3"

shift 3

mkdir -p "$DEST"

for N in {001..802}; do
	FILE="${PREFIX}${N}${SUFFIX}"
	bash getWikiFile.sh $@ "$FILE" "$DEST"
done
