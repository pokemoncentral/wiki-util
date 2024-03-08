#!/usr/bin/env bash

# This script downloads the wikicode of the passed pages from the specified
# wiki. The results are saved in files named after the page, in the specified
# directory.

# Arguments:
#   - $1: The file containing the list of pages. One title per line
#   - $2: The wiki to download from. Can be one of
#       bulba)
#           downloads from Bulbapedia
#	    pcwiki)
#		    downloads from Pokémon Central Wiki
#       pokewiki)
#           downloads from PokéWiki
#   - $3: The directory to save the files to. Defaults to './pags'

PAGES="$1"
BASE_URL=''
OUT_DIR="${3:-pages}"

case "$2" in
    'bulba')
        BASE_URL='https://bulbapedia.bulbagarden.net/w'
        ;;
    'pcwiki')
        BASE_URL='http://media.pokemoncentral.it/wiki'
        ;;
    'pokewiki')
        BASE_URL='http://www.pokewiki.de/images'
        ;;
    *)
        echo "Unknown wiki: $2"
        exit 1
        ;;
esac

if ! which jq &> /dev/null; then
    echo 'jq not installed!'
    exit 1
fi

mkdir -p "$OUT_DIR"

while read PAGE; do
    wget -O - "$BASE_URL/api.php\
?action=query\
&titles=$PAGE\
&format=json\
&prop=revisions\
&rvprop=content" \
        | jq -r '.query.pages[].revisions[0]["*"]' > "$OUT_DIR/$PAGE.txt"
done < "$PAGES"
