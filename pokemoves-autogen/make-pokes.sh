#!/bin/bash

source config.sh

CFLAG=false
LFLAG=false
SDIR="luamoves"
DOCKERV="pokemovesdb"
PORT=12345

repsrc=("farfetchd" "farfetchdG" "sirfetchd")
repdst=("farfetch'd" "farfetch'dG" "sirfetch'd")

while getopts "hcls:d:p:b:" o; do
    case "${o}" in
        h)
            echo "Options:
    -h       help, print this help
    -c       csv, recompute csv files from docker db.
    -l       lua, recompute lua files from csvs.
    -s DIR   source, source dir of single Pokémon tables.
             if DIR is equal to - it uses no source, only adds head and foot
    -d name  docker, name of the docker image with the right version of psql.
    -p num   port, port of the docker image running the db.
    -b POKE  begin, only recomputes csvs, and only from pokemon POKE onward.
             If this option is given, ignores -l"
            exit 0
            ;;
        c)
            CFLAG=true
            ;;
        l)
            LFLAG=true
            ;;
        s)
            SDIR="$OPTARG"
            ;;
        d)
            DOCKERV="$OPTARG"
            ;;
        p)
            PORT=$OPTARG
            ;;
        b)
            BEGIN=$OPTARG
            ;;
    esac
done
shift $((OPTIND-1))

get_index() {
    for i in "${!repsrc[@]}"; do
    	if [[ "${repsrc[$i]}" = "${1}" ]]; then
    	    return $i
    	fi
    done
    return -1
}

create_csv() {
    poke=$1
    docker run --rm --network=host --user $(id -u) \
               -v /etc/passwd:/etc/passwd:ro \
               -v $(pwd):/data "${DOCKERV}" \
               psql -h localhost -p $PORT -U postgres \
               -c "\\COPY
               (SELECT m.identifier, pmm.identifier, vg.generation_id, vg.identifier, pm.level
               FROM pokemon_moves AS pm JOIN pokemon AS p ON pm.pokemon_id = p.id
               JOIN pokemon_move_methods AS pmm ON pm.pokemon_move_method_id = pmm.id
               JOIN version_groups AS vg ON pm.version_group_id = vg.id
               JOIN moves AS m ON pm.move_id = m.id
               WHERE p.identifier = '${poke}'
               ORDER BY pmm.id, vg.generation_id, vg.id, pm.level) TO '/data/${TEMPOUTDIR}/pokecsv/${poke}.csv' WITH csv" > /dev/null
    chmod 644 "${TEMPOUTDIR}/pokecsv/${poke}.csv"
}

outfile="$OUTPUTMODULEDIR/${TMPMODULENAME}.lua"

if ! [[ -z ${BEGIN+x} ]]; then
    if [[ $CFLAG -ne "true" ]]; then
        echo "-b given, but not -c. Please explicitly ask to recompute csv files. Aborting"
        exit 1
    fi
    sed -e/"${BEGIN}"/\{ -e:1 -en\;b1 -e\} -ed $POKELIST | while read poke; do
        create_csv "$poke"
        echo "$poke"
    done
    exit 0
fi

# Truncate the file at the beginning of the script
# cat pokemoves-head > "$outfile"
echo "local m = {}" > "$outfile"
echo "" >> "$outfile"
if ! [[ $SDIR == "-" ]]; then
    while read poke; do
        if [[ $CFLAG == true ]]; then
            create_csv "${poke}"
        fi
        pokemodule=$poke
        get_index $poke $repsrc
        idx=$?
        if [[ $idx -ne 255 ]]; then
            if [[ $CFLAG == true ]]; then
                mv "${TEMPOUTDIR}/pokecsv/${poke}.csv" "${TEMPOUTDIR}/pokecsv/${repdst[$idx]}.csv"
            fi
            pokemodule=${repdst[$idx]}
        fi
        if [[ $LFLAG == true ]]; then
            lua "$LUASCRPITSDIR/csv2pokemoves.lua" "${pokemodule}" >> logs/csv-to-pokemoves.log
        fi
        cat "${TEMPOUTDIR}/${SDIR}/${pokemodule}.lua" >> "$outfile"
        echo "" >> "$outfile"
        if [[ $CFLAG == true ]] || [[ $LFLAG == true ]]; then
            echo "$pokemodule"
        fi
    done < $POKELIST
fi

echo "return m" >> "$outfile"
# cat pokemoves-foot >> "$outfile"
