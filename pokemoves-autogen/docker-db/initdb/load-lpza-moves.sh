#!/bin/bash

# This script load source csv in the db for Pokémon Legends: Z-A

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY lpza_moves
    FROM '/data/sourcecsv/lpza-moves.csv'
    WITH csv header delimiter '	'"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY lpza_move_params
    FROM '/data/sourcecsv/lpza-moves-params.csv'
    WITH csv header delimiter '	'"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY lpza_move_names
    FROM '/data/sourcecsv/lpza-move-names.csv'
    WITH csv header delimiter ','"
