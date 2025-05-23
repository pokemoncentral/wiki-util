# PokéMoves autogen
This directory contains scripts and data to automatically build PokéMoves-data,
the data module for learnlist and movelist.

## Create the data module
First you have to create a bash and a lua config file, copying the templates
`config-template.sh` to `config.sh` and `source-module-template.lua` to
`source-module.lua`, then setting values. Make sure the two are consistent.

After that, the script `create-pokemoves-data.sh` does all you need. You can
take a look at its options with `create-pokemoves-data.sh -h`.

## Get the learnlist
To get a learnlist for a given Pokémon, use `get-learnlist.lua` once you
created the data module as described above. For its usage, see its
documentation.

# Edit guide
How to add data, games, scripts and other things.

## Add data
The source of data are some files in the directory `docker-db/sourcecsv/`.
Right now there are only csv file, but any format that can be imported by
PostgreSQL is fine.

To add a new file you should:
- add the file in that directory (`docker-db/sourcecsv/`)
- add a psql command that loads it to `docker-db/load-pokes.sh`. You should
  probably add it at the bottom because of foreign key constraints, but of
  course it depends on your file.

Note that if you add new Pokémon, you must update the list of all Pokémon
(filename in `config.sh -> $POKELIST`).

## Add Pokémon
To add a new Pokémon, you should:
- add it to `docker-db/sourcecsv/pokemon.csv`
- add it to `lists/pokemon-names.list`
- in `lua-scripts/csv2pokemoves.lua`, update `baseNoBreed` (and possibly
  `breedNoBase`, but that's just to suppress a warning) as needed

## Add a game
To add data for a new game, you have to do the following things:
- add the csv source as explained above
- add the game row to `docker-db/sourcecsv/version_groups.csv`
- add the new Pokémons, as explained above
- update `learnlist-gen/print-learnlist-lib.lua`:
  - update `breedsgames`
- if a new gen, update `lua-scripts/csv2pokemoves.lua`:
  - add an empty table in `datagen`

## Update get-learnlist
It _should_ be enough to add the `learnlist-gen/print-learnlist<gen>.lua`.

## Create a csv from a datamine of Kurt's
Python scripts in the `convert-datamines` directory convert datamines to csv.
- `datamine2csv.py` takes a full datamine and creates a csv. In the datamine,
  move names should be in italian (use the macro), the first `======` should be
  removed and a `\n======` should be added at the end. Some alternative forms
  should be removed as well. Then you can use the script to build the csv.
  This doesn't work well with tutor, and possibly there are some constants to
  modify in the script's code (some things are hardcoded for current games).

NOTES (to be sorted):
- there are now two scripts since they changed format for BDSP datamines
- in the script, there's a `version_group_id` to change, because it describes
  the id of the game(s) version for that movelist line

# Tricks
A few tricks when things goes wrong.

## Problems while computing csv files
If at some point the script crashes or have any problem while computing csv
files, you aren't doomed to restart the computation from the beginning. You can
run
`./make-pokes.sh -d IMAGE -p PORT -cb POKE`
to restart the computation of csv files only from POKE. After that, you should
just run `create-pokemoves-data.sh` without any option to do the job.

## psql: server closed the connection unexpectedly
Right after creation it take sometime for postgres to load data, but I can't
find a way to get back control only after that time, so in
`create-pokemoves-data.sh` there is a sleep at the right point in the code.
Try increasing the sleep value in case you see the following error:
```
psql: server closed the connection unexpectedly
	This probably means the server terminated abnormally
	before or while processing the request.
```

# Dependencies
This repository has just a few dependencies other than standard bash scripting, that should
be installed on your system:
- Lua >=5.1 (any version you use for Wiki modules is fine)
- Docker >=18.9.5 (only 18.09.5 and 19.03.12 were actually tested)

# TODO
- Clean up config file: the two `MODULENAME` and `TMPMODULENAME` seem to be
  the same file, probably the TMP one is a remnant of when the module was
  moved to wiki-lua-modules directory.
- Change lua scripts to load only needed data, not the whole pokemoves-data
- Change `lua-scripts/csv2pokemoves.lua` so that `baseNoBreed` is only used to
  suppress a warning instead of being functionally required.

# Credits
Data in this this project are from:
- learnset until USUM (included) are from VeeKun's repository [pokedex](https://github.com/veekun/pokedex)
- learnset for LGPE and gen 8 are from [SciresM](https://twitter.com/SciresM/)'s and [Kaphotic](https://twitter.com/Kaphotics)'s datamines.
- learnset from SV are from [Slp32](https://pastebin.com/u/slp32).

Files in `docker-db/sourcecsv/` are made from those data.
