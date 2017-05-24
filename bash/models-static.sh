#!/bin/bash

# Arguments
# $1: the folder in which files are
# -u: uploads the file
# -g [xy, oras, roza]: game (only used when uploading)
# -m [path]: moves the files to path

declare -A games

games[xy]='X e Y'
games[oras]='Rubino Omega e Zaffiro Alpha'
games[roza]='Rubino Omega e Zaffiro Alpha'

upload=false
dest=.
while getopts "um:g:" opt; do
	case $opt in
		u)
			upload=true
			;;
		m)
			dest=$OPTARG
			;;
		g)
			game=${games[$OPTARG]}
			;;
	esac
done
source=${@:$OPTIND:1}

for file in $source/*.gif; do
	img=$(basename $file .gif)
	img=${img:3}.png
	convert $file[0] $dest/$img
	if $upload; then
		python $HOME/Files/pywikibot/pwb.py upload -keep -noverify $dest/$img {{I-Fairuse-3Dmodel-game-nocat}} [[Categoria:Modelli Pokémon statici $game]]
		rm $dest/$img
	fi
done
