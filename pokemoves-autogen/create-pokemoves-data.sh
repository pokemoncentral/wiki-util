#!/bin/bash

# This script runs the steps required to build module PokéMoves-data.lua

source config.sh

CFLAG=false
CONTAINER=""
DFLAG=false
PFLAG=false

while getopts "hcd:Dp" o; do
    case "${o}" in
        h)
            echo "Create data module PokéMoves-data from raw data.

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
  -D        same as -d using the default specified in config file
  -p        only processes lua file, without recomputing them from csv.
            Ignored with -c"
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
	    p)
	        PFLAG=true
	        ;;
    esac
done
shift $((OPTIND-1))

# First creates a dummy PokéMoves-data.lua with only m.games defined, needed by
# make-pokes.sh -l
./make-pokes.sh -s -

if [[ $CFLAG == true ]] || [[ ! -d "$TEMPOUTDIR/pokecsv" ]]; then
    echo "========================= Recomputing csv files =========================="

    # Setup the container to recompute csvs

    # If -d wasn't given or the container doesn't exists create a new container
    # and set $CONTAINER to the id (it's ok despite it not being the name)
    if [[ $DFLAG == false ]] || [[ -z $(docker ps -aqf "name=${CONTAINER}") ]]; then
        echo "=========================== Creating container ==========================="
        docker build -t pokemovesdb docker-db/
        CONTAINER=$(docker create -p ${CONTAINERPORT}:5432 --name "${CONTAINER}" -e"POSTGRES_HOST_AUTH_METHOD=trust" pokemovesdb)
        # In case of the following error, try increasing the sleep value
        # (see README for an explanation)
        #
        # psql: server closed the connection unexpectedly
        # 	This probably means the server terminated abnormally
        # 	before or while processing the request.
        docker start "$CONTAINER" > /dev/null
        sleep 25
    else
        docker start "$CONTAINER" > /dev/null
    fi

    # Compute level, tm and tutor
    mkdir -p "$TEMPOUTDIR/pokecsv"
    mkdir -p "$TEMPOUTDIR/luamoves"
    ./make-pokes.sh -cl -d pokemovesdb -p ${CONTAINERPORT}

    docker stop "$CONTAINER" > /dev/null
    # Remove the container if the script wasn't given -d
    if [[ $DFLAG == false ]]; then
        echo "=========================== Removing container ==========================="
        docker container rm "$CONTAINER"
    fi
elif [[ $PFLAG == false ]]; then
    # Compute level, tm and tutor
    mkdir -p "$TEMPOUTDIR/luamoves"
    ./make-pokes.sh -l
else
    ./make-pokes.sh -s "luamoves"
fi
./copy-modules.sh -s "$TEMPOUTDIR/luamoves"
echo "============ Updated PokéMoves-data.lua with level, tm and tutor ============="

# Make preevo
echo "=========================== Start computing preevo ==========================="
mkdir -p "$TEMPOUTDIR/luamoves-preevo"
lua "$LUASCRPITSDIR/recomp-preevo.lua"
./make-pokes.sh -s "luamoves-preevo"
./copy-modules.sh -s "$TEMPOUTDIR/luamoves-preevo"
echo "=================== Updated PokéMoves-data.lua with preevo ==================="

# Make breed
echo "=========================== Start computing breed ============================"
mkdir -p "$TEMPOUTDIR/luamoves-breed"
lua "$LUASCRPITSDIR/recomp-breed.lua"
./make-pokes.sh -s "luamoves-breed"
./copy-modules.sh -s "$TEMPOUTDIR/luamoves-breed"
echo "=================== Updated PokéMoves-data.lua with breed ===================="

# Compress
echo "============================= Start compressing =============================="
mkdir -p "$TEMPOUTDIR/luamoves-compress"
lua "$LUASCRPITSDIR/compress-pokemoves.lua"
echo "=================== PokéMoves-data.lua compressed ===================="

# Split Pokémon and copy them to the modules directory
echo "================================= Final copy ================================="
./copy-modules.sh -s "$TEMPOUTDIR/luamoves-compress"
echo "================================== Finished =================================="
