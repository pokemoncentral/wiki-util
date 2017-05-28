#!/bin/bash

# Uploads from Bulbapedia to Pokémon Central
# Wiki a batch of file having conscecutive
# ndexes in their name, skipping duplicates

# Arguments
#	- $1: Beginning ndex
#	- $2: Ending ndex
#	- $3: Source file pattern, must contain literal
#			$NDEX where the ndex should be placed
#	- $4: Destination file pattern, must contain literal
#			$NDEX where the ndex should be placed
#	- $5: Description, the same for all files being uploaded
#	- $6: Throttle for uploading, defaults to 5

BEG=$1
END=$(( $2 + 1 ))
SOURCE_PATTERN="$3"
DEST_PATTERN="$4"
DESC="$5"
PT=${6:-5}

# Three expression for is necessary because bash
# sequence built-in works only with literals

for (( NDEX=$BEG; NDEX < $END; ++NDEX )); do
	NDEX03=$(printf "%03d" $NDEX)
	SOURCE=${SOURCE_PATTERN//'$NDEX'/$NDEX03}
	DEST=${DEST_PATTERN//'$NDEX'/$NDEX03}
	echo n | bash get-wiki-file.sh -p $PT -w bulba -d wiki "$SOURCE" "$DEST" "$DESC"
done
