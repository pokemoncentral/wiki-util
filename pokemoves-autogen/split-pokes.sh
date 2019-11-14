#!/bin/bash

source config.sh

repsrc=("farfetchd" "farfetchdG" "sirfetchd")
repdst=("farfetch'd" "farfetch'dG" "sirfetch'd")

while getopts "hs:" o; do
    case "${o}" in
        h)
            echo "Usage:
split-pokes [OPTIONS]... [FILE]

This script merges files for many Pokémon to create module PokéMoves-data,
splitted in many actual modules because PCW doesn't support files too big.

All files are taken from a directory, and Pokémon names are listed in the
file ${POKELIST}. Group are created from patterns in splitpatterns,
and each group creates a different lua file.


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

get_index () {
    for i in "${!repsrc[@]}"; do
        if [[ "${repsrc[$i]}" = "${1}" ]]; then
            return $i
        fi
    done
    return -1
}

# Iterate for each splitting pattern
for f in ${POKELIST}.*; do
    j=${f##*.}
    outfile="${TMPMODULENAME}${j}.lua"

    # Truncate the file at the beginning of the script
    # cat pokemoves-head > "$outfile"
    echo "local m = {}" > "$outfile"
    echo "" >> "$outfile"
    echo "======== File $f ========"
    echo $outfile
    # grep "${splitpatterns[$i]}" "$POKELIST" | while read poke; do
    while read poke; do
        pokemodule=$poke
        get_index $poke $repsrc
        idx=$?
        if [[ $idx -ne 255 ]]; then
            pokemodule=${repdst[$idx]}
        fi
        cat "${SDIR}/${pokemodule}.lua" >> "$outfile"
        echo "" >> "$outfile"
    done < $f

    echo "return m" >> "$outfile"
    # cat pokemoves-foot >> "$outfile"

    echo "$MODULESPATH/${MODULENAME}-${j}.lua"
    cp "$outfile" "$MODULESPATH/${MODULENAME}-${j}.lua"
done
