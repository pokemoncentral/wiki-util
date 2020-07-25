#!/bin/bash

# This script load source csv in the db for Pokémon moves

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY moves
    FROM '/data/sourcecsv/moves.csv'
    WITH csv header"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY pokemon
    FROM '/data/sourcecsv/pokemon.csv'
    WITH csv header"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY pokemon_move_methods
    FROM '/data/sourcecsv/pokemon_move_methods.csv'
    WITH csv header"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY version_groups
    FROM '/data/sourcecsv/version_groups.csv'
    WITH csv header"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY pokemon_moves
    FROM '/data/sourcecsv/pokemon_moves.csv'
    WITH csv header"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY pokemon_moves
    FROM '/data/sourcecsv/tutor_moves_usum.csv'
    WITH csv"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY pokemon_moves
    FROM '/data/sourcecsv/breed_alolan_usum.csv'
    WITH csv"

psql -p 5432 -U "$POSTGRES_USER" -d postgres \
    -c "\\COPY pokemon_moves
    FROM '/data/sourcecsv/pokemon_moves_spsc_ioa.csv'
    WITH csv"

# psql -p 5432 -U "$POSTGRES_USER" -d postgres \
#     -c "\\COPY pokemon_moves
#     FROM '/data/sourcecsv/tutor_moves_spsc.csv'
#     WITH csv header"
