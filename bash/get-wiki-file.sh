#!/bin/bash

# Downloads a file from Bulbapedia, PokéWiki,
# or Pkoémon Central Wiki, saving it locally
# or uploading it to Bulbapedia

# Arguments

# -d:
# 	local)
#		save locally
#	wiki)
#		upload immediately to pcw

# -w:
#	bulba)
#		downloads from Bulbapedia
#	pcwiki)
#		downloads from Pokémon Central Wiki
#	pokewiki)
#		downloads from PokéWiki

# -p: Flag. If enabled, sets the
#		bot throttle to 1

# $1: source filename

# $2:
#	d == 'local')
#		destination path.
#		If it contains a dot, it's regarded
#		as a file path, otherwise as a directory.
#		In the former case the downloaded file
#		will have the provided name, while in
#		the latter it will be downloaded in the
#		specified directory with its remote name.
#	d == 'wiki')
#		destination filename

# $3: description, only useful when d == 'wiki'

DEST=''
BASE_URL=''
PT=''

while getopts "d:w:p" OPTION; do
	case $OPTION in
		d)
			case "local wiki" in
				*$OPTARG*)
					DEST=$OPTARG
					;;
				*)
					echo You messed up with something
					exit 1
					;;
			esac
			;;
		w)
			case $OPTARG in
				bulba)
					BASE_URL='http://cdn.bulbagarden.net/upload'
					;;
				pcwiki)
					BASE_URL='http://media.pokemoncentral.it/wiki'
					;;
				pokewiki)
					BASE_URL='http://www.pokewiki.de/images'
					;;
				*)
					echo Unknown wiki: $OPTARG
					exit 1
					;;
			esac
			;;
		p)
			PT='-putthrottle:1'
			;;
			
		*)	# getopts already printed error message
			exit 1
			;;
	esac
done

if [[ -z $DEST ]]; then
	echo No destination specified. Aborting.
	exit 1
fi

shift $(( $OPTIND - 1 ))

FILENAME="$1"
DEST_PATH="$2"

MD5=$(echo -n "$FILENAME" | md5sum -)
FILE_URL=$(echo -n $BASE_URL/${MD5:0:1}/${MD5:0:2}/$FILENAME | uni2ascii -aJ)

if [[ $DEST == 'local' ]]; then
	if [[ -n $(grep \\. <<<$DEST_PATH) ]]; then
		mkdir $(basename "$DEST_PATH")
		curl $FILE_URL > "$DEST_PATH"
	else
		mkdir -p "$DEST_PATH"
		cd "$DEST_PATH"
		curl -O $FILE_URL
		cd - > /dev/null
	fi
else
	python $PYWIKIBOT_DIR/pwb.py upload $PT -keep -noverify -filename:"$2" $FILE_URL "$3"
fi
