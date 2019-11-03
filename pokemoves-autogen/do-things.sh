#!/bin/bash

# This script runs the steps required to build module PokéMoves-data.lua

source config.sh

CFLAG=false
CONTAINER=""
DFLAG=false

while getopts "hcd:D" o; do
    case "${o}" in
        h)
            echo "Compute data module PokéMoves-data

Options:
  -h        print this help
  -c        force the script to recompute csv files for all Pokémon.
            The script recompute them if either this flag is given or
            directory \"pokecsv\" doesn't exists. If the script doesn't
            recompute them it also doesn't create/start the container
  -d name   name of the docker container with the moves db.
            If not given, it creates a new container and removes it after
            the execution. If given but the container doesn't exists the
            script creates and fills it.
            If the script doesn't need to create the container (eg:
            because it doesn't have to recompute csv) this argument
            is ignored.
  -D        same as -d using the default specified in config file"
            exit 0
            ;;
        c)
            CFLAG=true
            ;;
        d)
            CONTAINER="$OPTARG"
            DFLAG=true
            ;;
        D)
            CONTAINER="$CONTAINERDEFAULTNAME"
            DFLAG=true
            ;;
    esac
done
shift $((OPTIND-1))


# Add the lua modules dir in order to allow lua scripts to source them
sed -e 's:    ";/path/to/lua/modules/?.lua":    ";'"${MODULESPATH}"'/?.lua":' \
    -e 's:pokemoves = require("pokemoves-data"):pokemoves = require("'"${TMPMODULENAME}"'"):' \
    source-modules.lua.base > source-modules.lua
chmod 644 source-modules.lua

# First creates a dummy PokéMoves-data.lua with only m.games defined, needed by
# make-pokes.sh -l
./make-pokes.sh -s -

if [[ $CFLAG == true ]] || [[ ! -d pokecsv ]]; then
    echo "========================= Recomputing csv files =========================="

    # Setup the container to recompute csvs

    # If -d wasn't given or the container doesn't exists create a new container
    # and set $CONTAINER to the id (it's ok despite it not being the name)
    if [[ $DFLAG == false ]] || [[ -z $(docker ps -aqf "name=${CONTAINER}") ]]; then
        echo "=========================== Creating container ==========================="
        docker build -t pokemovesdb docker-db/
        CONTAINER=$(docker create -p ${CONTAINERPORT}:5432 --name "${CONTAINER}" pokemovesdb)
        # Right after creation it take sometime for postgres to load data, but
        # I can't find a way to get back control only after that time, so this
        # sleep workaround.
        # In case of the following error, try increasing the sleep value
        #
        # psql: server closed the connection unexpectedly
        # 	This probably means the server terminated abnormally
        # 	before or while processing the request.
        docker start "$CONTAINER" > /dev/null
        sleep 20
    else
        docker start "$CONTAINER" > /dev/null
    fi

    # Compute level, tm and tutor
    mkdir -p pokecsv
    mkdir -p luamoves
    ./make-pokes.sh -cl -d pokemovesdb -p ${CONTAINERPORT}

    docker stop "$CONTAINER" > /dev/null
    # Remove the container if the script wasn't given -d
    if [[ $DFLAG == false ]]; then
        echo "=========================== Removing container ==========================="
        docker container rm "$CONTAINER"
    fi
else
    # Compute level, tm and tutor
    mkdir -p luamoves
    ./make-pokes.sh -l
fi
echo "============ Updated PokéMoves-data.lua with level, tm and tutor ============="

# Make preevo
echo "=========================== Start computing preevo ==========================="
mkdir -p luamoves-preevo
./recomp-preevo.lua
./make-pokes.sh -s luamoves-preevo
echo "=================== Updated PokéMoves-data.lua with preevo ==================="

# Make breed
echo "=========================== Start computing breed ============================"
mkdir -p luamoves-breed
./recomp-breed.lua
# ./make-pokes.sh -s luamoves-breed
echo "=================== Updated PokéMoves-data.lua with breed ===================="

# Split Pokémon and copy them to the modules directory
echo "=========================== Splitting and copying ============================"
./split-pokes.sh -s luamoves-breed
echo "================================== Finished =================================="
