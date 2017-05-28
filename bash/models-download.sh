#!/bin/bash

# Arguments:
# variant [shiny, back, back_shiny, normal]
# game [xy, oras, sm];

# Simple constants
PP_BASE_URL='http://www.pkparaiso.com/imagenes'
LOG_FILE='models_download.log'

# Pkparaiso games mapping
declare -A PP_GAMES
PP_GAMES[xy]='xy'
PP_GAMES[oras]='rubi-omega-zafiro-alfa'
PP_GAMES[sm]='sol-luna'

# Pkparaiso variants mapping
declare -A PP_VARIANTS
PP_VARIANTS[shiny]='-shiny'
PP_VARIANTS[back]='-espalda'
PP_VARIANTS[back_shiny]='-espalda-shiny'
PP_VARIANTS[normal]=''

# PokéWiki games mapping
declare -A GC_GAMES
GC_GAMES[xy]='XY'
GC_GAMES[oras]='ORAS'
GC_GAMES[sm]='SoMo'

# PokéWiki variants mapping
declare -A GC_VARIANTS
GC_VARIANTS[shiny]='Schillernd_'
GC_VARIANTS[back]='Rückseite_'
GC_VARIANTS[back_shiny]='Rückseite_Schillernd_'
GC_VARIANTS[normal]=''

# Input processing
VARIANT=${1,,}
GAMES=${2,,}

# Utility variables
PP_URL=$PP_BASE_URL/${PP_GAMES[$GAMES]}/sprites/animados${PP_VARIANTS[$VARIANT]}
DROPBOX_BASE_DIR=~/Dropbox/Wiki/Sprite/Modelli_$GAMES
LISTFILE=$DROPBOX_BASE_DIR/modellist-$VARIANT.txt
DROPBOX_DIR=$DROPBOX_BASE_DIR/$VARIANT

# Prints on both STDOUT and log file
function print {
	echo $1 | tee -a $LOG_FILE
}

# Moves all gif files in a temporary
# directory to Dropbox
function moveToDropbox {
	TEMP_DIR=Dl$1

	bash delete-by-type.sh $TEMP_DIR gif

	ls -1 $TEMP_DIR >> $LISTFILE
	mv $TEMP_DIR/* $DROPBOX_DIR
}

# Fetching Pokèmon data
. spritesPokeList.sh

# Dropbox destination
mkdir -p $DROPBOX_DIR

# Creating list file if it does not exist
touch $LISTFILE

# Temporary directories
mkdir -p Dlm
mkdir -p Dlf

# Log file
:> $LOG_FILE

for GC_NAME in {710,711}{,a,b,c}; do
# for GC_NAME in "${!pokemon[@]}"; do
	PP_NAME=${pokemon[$GC_NAME]}

	# Male and female PCW sprite names
	MALE_NAME=$(bash models-rename.sh $PP_NAME.gif $VARIANT m $GAMES)
	FEMALE_NAME=$(bash models-rename.sh $PP_NAME.gif $VARIANT f $GAMES)

    # Male and female destination paths
    MALE_DEST=Dlm/$MALE_NAME
    FEMALE_DEST=Dlf/$FEMALE_NAME

	# If something went wrong, skipping Pokèmon
	if [[ $MALE_NAME =~ wrong || $FEMALE_NAME =~ wrong ]]; then
		print "$PP_NAME failed to be renamed"
		continue
	fi

	# If both files exsist, skipping
	if [[ -n $(grep $FEMALE_NAME $LISTFILE) ]]; then
		print "Abort downloading: $PP_NAME $VARIANT female target filename already exists"
		FEMALE_EXISTS=true
	else
		FEMALE_EXISTS=false
	fi
	if [[ -n $(grep $MALE_NAME $LISTFILE) ]]; then
		print "Abort downloading: $PP_NAME $VARIANT male target filename already exists"
		MALE_EXISTS=true
	else
		MALE_EXISTS=false
	fi
	[[ $FEMALE_EXISTS == true && $MALE_EXISTS == true ]] && continue

	# Pkparaiso download

	# Male
	if [[ $MALE_EXISTS == false ]]; then
        curl $PP_URL/$PP_NAME.gif > $MALE_DEST
    fi

	# Female
	if [[ $FEMALE_EXISTS == false ]]; then
        curl $PP_URL/$PP_NAME-f.gif > $FEMALE_DEST
    fi

	# Other animation
	for K in {2..5}; do
		ANI_NAME=$(bash models-rename.sh $PP_NAME-$K.gif $VARIANT m $GAMES)
		if [[ -z $(grep $ANI_NAME $LISTFILE) ]]; then
            ANI_DEST=Dlm/$ANI_NAME
            curl $PP_URL/$PP_NAME-$K.gif > $ANI_DEST
        fi
	done

	# Skipping PokéWiki what already
    # downloaded from Pkparaiso

    [[ -e $MALE_DEST ]] && MALE_EXISTS=true
    [[ -e $FEMALE_DEST ]] && FEMALE_EXISTS=true
    [[ $MALE_EXISTS == true && $FEMALE_EXISTS == true ]] \
        && continue

	# PokéWiki download

	GC_SPR="Pokémonsprite_${GC_NAME}_${GC_VARIANTS[$VARIANT]}${GC_GAMES[$GAMES]}"
    
	# Male and female

	# Male
	if [[ $MALE_EXISTS == false ]]; then
        bash get-wiki-file.sh -d local -w pokewiki $GC_SPR.gif Dlm
    fi

	# Female
	if [[ $FEMALE_EXISTS == false ]]; then
        GC_SPR="Pokémonsprite_${GC_NAME}_Weiblich_${GC_VARIANTS[$VARIANT]}${GC_GAMES[$GAMES]}"
        bash get-wiki-file.sh -d local -w pokewiki $GC_SPR.gif Dlf
    fi

done

# Moving downloaded files to dropbox
moveToDropbox m
moveToDropbox f

# Clearing temporary stuff
rm -rf Dlm
rm -rf Dlf
