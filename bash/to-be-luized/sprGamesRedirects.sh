#!/bin/bash

# Creates sprites redirects for a single
# Pokémon, handling one gender at a time
# and forms differences: they are appended
# to a file in the format accepted by
# pywikibot pagefromfile script.

# Parameters:
#	- $1: ndex of the Pokémon
#	- $2: Gender of the Pokémon
#	- $3: Forms of the Pokémon, given as a
#		 space separated list of abbreviations
#	- $4: name of the Pokémon, only used in comments

# These variables coul have been arguments,
# but since this script is meant to be used
# repeatedly to add redirects to the same
# file for many forms from and to the same
# games, they are better as variables

FROM_GAME='xy'
TO_GAME='roza'
OUTFILE=$HOME/rozaModelsRedirects.txt

# This function prints a redirect to a file
# given too many parameters to create it

function makeRedirect {
	local FROM_GAME=$1
	local TO_GAME=$2
	local PREFIX=$3
	local NDEX=$4
	local VARIANT=$5
	local FORM=$6
	local EXT=$7
	local OUTFILE="$8"

	echo -e "{{-start-}}\n'''File:$PREFIX$TO_GAME$VARIANT$NDEX$FORM.$EXT'''\n#RINVIA[[File:$PREFIX$FROM_GAME$VARIANT$NDEX$FORM.$EXT]]\n{{-stop-}}" >> "$OUTFILE"
}

NDEX=$1
SEX=$2
FORMS="$3"
NAME="$4"

[[ $SEX == 'f' ]] && EXTENDED_SEX='female' || EXTENDED_SEX='male'

echo "$NAME $EXTENDED_SEX normal and shiny redirects"
makeRedirect $FROM_GAME $TO_GAME 'Spr' $NDEX $SEX '' '.gif' $OUTFILE
makeRedirect $FROM_GAME $TO_GAME 'Spr' $NDEX "${SEX}sh" '' '.gif' $OUTFILE

echo "$NAME $EXTENDED_SEX static redirect"
makeRedirect $FROM_GAME $TO_GAME '' $NDEX $SEX '' '.png' $OUTFILE

if [[ -n $FORMS ]]; then
	echo "$NAME $EXTENDEX_SEX alternate forms normal and shiny redirects"
	for FORM in ${FORMS[@]}; do
		makeRedirect $FROM_GAME $TO_GAME 'Spr' $NDEX $SEX $FORM '.gif' $OUTFILE
		makeRedirect $FROM_GAME $TO_GAME 'Spr' $NDEX "${SEX}sh" $FORM '.gif' $OUTFILE
	done

	echo "$NAME $EXTENDED_SEX alternate forms static redirect"
	for FORM in ${FORMS[@]}; do
		makeRedirect $FROM_GAME $TO_GAME '' $NDEX $SEX $FORM '.png' $OUTFILE
	done
fi
