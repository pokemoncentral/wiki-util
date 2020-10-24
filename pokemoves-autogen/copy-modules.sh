#!/bin/bash

source config.sh

repsrc=("farfetchd" "farfetchdG" "sirfetchd")
repdst=("farfetch'd" "farfetch'dG" "sirfetch'd")

while getopts "hs:" o; do
    case "${o}" in
        h)
            echo "Usage:
copy-module [-h] -s SOURCEDIR

This script merges files for many Pokémon to create module PokéMoves-data,
possibly splitting the among many actual modules because PCW doesn't support
files too big. After that, it copies the result in the wiki modules directory

All files are taken from the directory specified by the (mandatory) parameter
-s, and Pokémon names are listed in the file ${POKELIST}. Group are created
from patterns in splitpatterns, and each group creates a different lua file.

Options:
    -h       help, print this help
    -s DIR   source, source dir of single Pokémon tables"
            exit 0
            ;;
        s)
            SDIR="$OPTARG"
            ;;
    esac
done
shift $((OPTIND-1))

if [[ -z ${SDIR+x} ]]; then
    echo "No source directory specified, aborting"
    exit 1
fi

get_index () {
    for i in "${!repsrc[@]}"; do
        if [[ "${repsrc[$i]}" = "${1}" ]]; then
            return $i
        fi
    done
    return -1
}

# Join all files listed in the file specified by the first parameter, and
# put the result in the files specified by the second
join_files() {
    list=$1
    outfile=$2

    echo "local m = {}" > "$outfile"
    echo "" >> "$outfile"
    echo "======== List $list ========"
    echo "Output in $outfile"
    while read poke; do
        pokemodule=$poke
        get_index $poke $repsrc
        idx=$?
        if [[ $idx -ne 255 ]]; then
            pokemodule=${repdst[$idx]}
        fi
        cat "${SDIR}/${pokemodule}.lua" >> "$outfile"
        echo "" >> "$outfile"
    done < $list

    echo "return m" >> "$outfile"
}


# Determines the list files depending on the value of $SPLIT
if [[ "$SPLIT" == "no" ]]; then
    outfile="${TMPMODULENAME}.lua"

    join_files "$POKELIST" "$outfile"

    echo "$OUTPUTMODULEDIR/${MODULENAME}.lua"
    cp "$outfile" "$OUTPUTMODULEDIR/${MODULENAME}.lua"
else
    # Iterate for each splitting pattern
    for f in ${POKELIST}.*; do
        j=${f##*.}
        outfile="${TMPMODULENAME}${j}.lua"

        join_files "$f" "$outfile"

        echo "$OUTPUTMODULEDIR/${MODULENAME}-${j}.lua"
        cp "$outfile" "$OUTPUTMODULEDIR/${MODULENAME}-${j}.lua"
    done
fi
