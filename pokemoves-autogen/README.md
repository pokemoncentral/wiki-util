# PokéMoves autogen
This directory contains scripts and datas to automatically build PokéMoves-data,
the data module for learnlist and movelist.

## Create the data module
First you have to create a config file, copying the template `config-template.sh`
to `config.sh` and setting values.

After that, the script `do-things.sh` takes care of anything. Just take a look at
its options using `do-things.sh -h` before running it because it involves creating
(and afterward destroying) containers, so you want to make sure it doesn't clash
with anything already on your system.

## Add data
The source of data are some files in the directory `docker-db/sourcecsv/`. Right
now there are only csv file, but any format that can be imported by PostgreSQL is fine.

To add a new file you should:
- add the file in that directory (`docker-db/sourcecsv/`, in case you have short memory).
- add a psql command that loads it to `docker-db/load-pokes.sh`. You should probably add
  it at the bottom because of foreign key constraints, but you can decide it on your own
  depending on your file.

## Create a csv from a datamine of Kurt's
The python scripts here are only used to convert datamines to csv in some way.
- `datamine2csv.py` takes a full datamine and creates a csv. In the datamine,
  move names should be in italian (use the macro), the first `======` should be
  removed and a `\n======` should be added at the end. Some alternative forms
  should be removed as well. Then you can use the script to build the csv.
  This doesn't work well with tutor, and possibly there are some constants to
  modify in the script's code (some things are hardcoded for current games).

## Tricks
### Problems while computing csv files
If at some point the script crashes or have any problem while computing csv files,
you aren't doomed to restart the computation from the beginning. You can run
`./make-pokes.sh -d IMAGE -p PORT -cb POKE`
to restart the computation of csv files only from POKE. After that, you should
just run `do-things.sh` without any option to do the job.

### psql: server closed the connection unexpectedly
Right after creation it take sometime for postgres to load data, but I can't
find a way to get back control only after that time, so in `do-things.sh` there
is a sleep at the right point in the code.
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
- Move lists in a subdir (`pokemon-names.txt*`)
- Move `pokemoves-data.lua` (the output) in the appropriate subdir

# Credits
Data in this this project are from:
- learnset until USUM (included) are from VeeKun's repository [pokedex](https://github.com/veekun/pokedex)
- learnset for LGPE and gen 8 (both games and DLC) are from [SciresM](https://twitter.com/SciresM/)'s and [Kaphotic](https://twitter.com/Kaphotics)'s datamines.

Files in `docker-db/sourcecsv/` are made from those data.
