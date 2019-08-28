#!/bin/bash

# This script runs the steps required to build module PokéMoves-data.lua

# Path to repository pokemoncentral/wiki-lua-modules
MODULESPATH="/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-lua-modules/"

# Create and start the db docker
cd docker-db
docker build -t pokemovesdb .
docker stop moves-db && docker container rm moves-db
docker run --name moves-db -p 12345:5432 -d pokemovesdb
# Right after creation it take sometime for postgres to load data, but
# I can't find a way to get back control only after that time, so this sleep
# workaround.
# In case of the following error, try increasing the sleep value:
# psql: server closed the connection unexpectedly
# 	This probably means the server terminated abnormally
# 	before or while processing the request.
# TEST
# sleep 20
cd ..

# Run scripts in order
# TODO: change source-modules.lua to use $MODULESPATH

# First creates a dummy PokéMoves-data.lua with only m.games defined, needed by
# make-pokes.sh -l
./make-pokes.sh -s -
cp pokemoves-data.lua $MODULESPATH/PokéMoves-data.lua

# Make level, tm and tutor
mkdir -p pokecsv
mkdir -p luamoves
# TEST
# ./make-pokes.sh -cl -d pokemovesdb -p 12345
./make-pokes.sh -l
# TODO: at some point here, I should fix mew with alltm
cp pokemoves-data.lua $MODULESPATH/PokéMoves-data.lua

# Make preevo
echo "=========================== Start computing preevo ==========================="
mkdir -p luamoves-preevo
./recomp-preevo.lua
./make-pokes.sh -s luamoves-preevo
cp pokemoves-data.lua $MODULESPATH/PokéMoves-data.lua
echo "=================== Updated PokéMoves-data.lua with preevo ==================="

# Make breed
echo "=========================== Start computing breed ============================"
mkdir -p luamoves-breed
./recomp-breed.lua
./make-pokes.sh s luamoves-breed
cp pokemoves-data.lua $MODULESPATH/PokéMoves-data.lua
echo "=================== Updated PokéMoves-data.lua with breed ===================="
