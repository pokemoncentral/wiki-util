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

## Add datas
The source of data are some files in the directory `docker-db/sourcecsv/`. Right
now there are only csv file, but any format that can be imported by PostgreSQL is fine.

To add a new file you should:
- add the file in that directory (`docker-db/sourcecsv/`, in case you have short memory).
- add a psql command that loads it to `docker-db/load-pokes.sh`. You should probably add
  it at the bottom because of foreign key constraints, but you can decide it on your own
  depending on your file.

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
In case of the following error, try increasing the sleep value

psql: server closed the connection unexpectedly
	This probably means the server terminated abnormally
	before or while processing the request.

# Dependencies
This repository has just a few dependencies other than standard bash scripting, that should
be installed on your system:
- Lua 5.1 (actually any version you use for Wiki modules should be fine, but only 5.1 was tested)
- Docker (any version should be fine, but only 18.09.5 was tested)
