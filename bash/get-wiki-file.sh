#!/bin/bash

# Downloads a file from Bulbapedia, PokéWiki,
# Poképedia or Pokémon Central Wiki, saving
# it locally or uploading it to Bulbapedia

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
#	pokepedia)
#		downloads from Poképedia
#   wikidex)
#       downloads from WikiDex

# -p: Flag. If enabled, sets the
#		bot throttle to 1

# -b: Flag. If enabled, tries to
#       use the custom pwb script
#       imagedownload. Only works
#       with -d local


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
LANG=''
PT=''
USEPWB='no'

while getopts "d:w:pb" OPTION; do
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
					BASE_URL='http://cdn2.bulbagarden.net/upload'
                    LANG='en'
					;;
				pcwiki)
					BASE_URL='http://media.pokemoncentral.it/wiki'
                    LANG='it'
					;;
				pokewiki)
					BASE_URL='http://www.pokewiki.de/images'
                    LANG='de'
					;;
				pokepedia)
					BASE_URL='https://www.pokepedia.fr/images'
                    LANG='fr'
					;;
                wikidex)
                    BASE_URL='https://images.wikidexcdn.net/mwuploads/wikidex'
                    LANG='es'
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
        b)
            USEPWB='yes'
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

if [[ $USEPWB == 'yes' ]] && [[ $DEST -ne 'local' ]]; then
    echo "Can't use pwb (-b) if destination isn't local"
    exit 1
fi

shift $(( $OPTIND - 1 ))

FILENAME="$1"
DEST_PATH="$2"

MD5=$(echo -n "$FILENAME" | md5sum -)
FILE_URL=$(echo -n $BASE_URL/${MD5:0:1}/${MD5:0:2}/$FILENAME | uni2ascii -aJ)

if [[ $DEST == 'local' ]]; then
	if [[ -n $(grep \\. <<<$DEST_PATH) ]]; then
		mkdir -p $(dirname "$DEST_PATH")
        if [[ "$USEPWB" == 'yes' ]]; then
            python $PYWIKIBOT_DIR/pwb.py imagedownload -pt:0 -lang:"$LANG" \
                   -target:"$(dirname "$DEST_PATH")" "File:$1"
            mv "$(dirname "$DEST_PATH")/$1" "$DEST_PATH"
        else
		    curl -L -A firefox $FILE_URL > "$DEST_PATH" 2> /dev/null
        fi
	else
		mkdir -p "$DEST_PATH"
        if [[ "$USEPWB" == 'yes' ]]; then
            python $PYWIKIBOT_DIR/pwb.py imagedownload -pt:0 -lang:"$LANG" -target:"$DEST_PATH" "File:$1"
        else
            cd "$DEST_PATH"
            curl -L -A firefox -O $FILE_URL 2> /dev/null
            cd - > /dev/null
        fi
	fi
else
	python $PYWIKIBOT_DIR/pwb.py upload $PT -keep -noverify -filename:"$2" $FILE_URL "$3"
fi
