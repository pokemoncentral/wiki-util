#!/bin/bash

# This script downloads missing 3D
# models for all variants of a given
# game.

# Arguments
#	- g: Game. One of:
#		- xy
#		- oras
#		- roza
#		- sm
#		- sl
#	- h: flag, halts the system once
#		done downloading

GAME=''
HALT=false

while getopts "g:h"; do
	case $OPTION in
		g)
			GAME=$OPTARG
			;;
		h)
			HALT=true
			;;
		*) # getopts already printed error message
			exit 1
			;;
	esac
done

cd $(dirname $0)

for VARIANT in normal shiny back back_shiny; do
	bash models-download.sh $VARIANT $GAME
done

[[ $HALT == true ]] && halt -p
