#!/bin/bash

# This script downloads a single set
# of 3D models from pkparaiso.com, using
# pokewiki.de as a backup source.

# A single set of models is identified
# by the category of those and the game
# they are from. Both genders are downloaded,
# including additional attacks.

# The models are saved in two directories
# in the current path, one for males and the
# other for females: files are further divided
# in subdirectories based on game and variant.

# The list of already downloaded sprites
# is kept in a file, to avoid the expensive
# process of downloading files twice

# Arguments:
# 	- $1: Variant. One of:
#		- shiny
#		- back
#		- back_shiny
#		- normal
#	- $2: Game. One of:
#		- xy
#		- oras
#		- roza
#		- sm
#		- sl

# Simple constants
PP_BASE_URL='http://www.pkparaiso.com/imagenes'
SHOWDOWN_BASE_URL='https://play.pokemonshowdown.com/sprites/'
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

# Showdown games mapping
declare -A SHOWDOWN_GAMES
SHOWDOWN_GAMES[xy]='xy'
SHOWDOWN_GAMES[oras]='xy'
SHOWDOWN_GAMES[sm]='xy'

# Showdown variants mapping
declare -A SHOWDOWN_VARIANTS
SHOWDOWN_VARIANTS[shiny]='shiny'
SHOWDOWN_VARIANTS[back]='back'
SHOWDOWN_VARIANTS[back_shiny]='back-shiny'
SHOWDOWN_VARIANTS[normal]=''

# Input processing
VARIANT=${1,,}
GAMES=${2,,}

# Utility variables
PP_URL=$PP_BASE_URL/${PP_GAMES[$GAMES]}/sprites/animados${PP_VARIANTS[$VARIANT]}
SHOWDOWN_URL=$SHOWDOWN_BASE_URL/${SHOWDOWN_GAMES[$GAMES]}ani-${SHOWDOWN_VARIANTS[$VARIANT]}
DROPBOX_BASE_DIR=~/Dropbox/Wiki/Sprite/Modelli_$GAMES
LISTFILE=$DROPBOX_BASE_DIR/modellist-$VARIANT.txt
MALE_PATH=Dlm/$GAMES/$VARIANT
FEMALE_PATH=Dlf/$GAMES/$VARIANT

# Prints on both STDOUT and log file
function print {
	echo $1 | tee -a $LOG_FILE
}

# Temporary directories
mkdir -p $MALE_PATH
mkdir -p $FEMALE_PATH

# Log file
:> $LOG_FILE

while read -a LINE; do
    GC_NAME=${LINE[0]}
	PP_NAME=${LINE[1]}
	SD_NAME=${LINE[2]}

	# Male and female PCW sprite names
	cd ../lua
	MALE_NAME=$(lua run.lua models-rename.lua $PP_NAME.gif $VARIANT m $GAMES)
	FEMALE_NAME=$(lua run.lua models-rename.lua $PP_NAME.gif $VARIANT f $GAMES)
	cd - > /dev/null

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

    # Male and female destination paths
    MALE_DEST=$MALE_PATH/$MALE_NAME
    FEMALE_DEST=$FEMALE_PATH/$FEMALE_NAME

	# Pkparaiso download

	# Male
	if [[ $MALE_EXISTS == false ]]; then
        curl -R $PP_URL/$PP_NAME.gif > $MALE_DEST 2> /dev/null
        bash delete-by-type.sh $MALE_DEST gif
    fi

	# Female
	if [[ $FEMALE_EXISTS == false ]]; then
        curl -R -R $PP_URL/$PP_NAME-f.gif > $FEMALE_DEST 2> /dev/null
        bash delete-by-type.sh $FEMALE_DEST gif
    fi

	# Other animation
	for K in {2..5}; do
		cd ../lua
		ANI_NAME=$(lua run.lua models-rename.lua $PP_NAME-$K.gif $VARIANT m $GAMES)
		cd - > /dev/null
		if [[ -z $(grep $ANI_NAME $LISTFILE) ]]; then
            ANI_DEST=$MALE_PATH/$ANI_NAME
            curl -R $PP_URL/$PP_NAME-$K.gif > $ANI_DEST 2> /dev/null
            bash delete-by-type.sh $ANI_DEST gif
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
        bash get-wiki-file.sh -d local -w pokewiki $GC_SPR.gif $MALE_DEST
        bash delete-by-type.sh $MALE_DEST gif
    fi

	# Female
	if [[ $FEMALE_EXISTS == false ]]; then
        GC_SPR="Pokémonsprite_${GC_NAME}_Weiblich_${GC_VARIANTS[$VARIANT]}${GC_GAMES[$GAMES]}"
        bash get-wiki-file.sh -d local -w pokewiki $GC_SPR.gif $FEMALE_DEST
        bash delete-by-type.sh $FEMALE_DEST gif
    fi

    [[ -e $MALE_DEST ]] && MALE_EXISTS=true
    [[ -e $FEMALE_DEST ]] && FEMALE_EXISTS=true
    [[ $MALE_EXISTS == true && $FEMALE_EXISTS == true ]] \
        && continue

    # Showdown download

	# Male
	if [[ $MALE_EXISTS == false ]]; then
        curl -R $SHOWDOWN_URL/$SD_NAME.gif > $MALE_DEST 2> /dev/null
        bash delete-by-type.sh $MALE_DEST gif
    fi

	# Female
	if [[ $FEMALE_EXISTS == false ]]; then
        curl -R SHOWDOWN_URL/$SD_NAME-f.gif > $FEMALE_DEST 2> /dev/null
        bash delete-by-type.sh $FEMALE_DEST gif
    fi

done < sprites-source.list

# Updating list files
ls -1 $MALE_PATH >> $LISTFILE
ls -1 $FEMALE_PATH >> $LISTFILE
