"""File to import data from csv."""

import csv
import re
import logging

CSV_DIR = "/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-util/pokemoves-autogen/intermediate-outputs/movecsv/"

def get_ndex(id, name):
    """Given the id of the db and the name compute the ndex."""
    if int(id) < 10000:
        return id.zfill(3)
    else:
        try:
            abbr = re.split('(?=[A-Z])', name, maxsplit=1)[1]
            # TODO the ndex is not id.zfill(3)
            return id.zfill(3) + abbr
        except IndexError:
            logging.error("id greater than 10000 and name without abbr: " + id + " - " + name)
            raise

def level_sort_key(lvl):
    """Changes a level to its sorting key."""
    lvl = int(lvl)
    if lvl == 0:
        return 1
    if lvl == 1:
        return 0
    return lvl

def level_mapper(lvl):
    """Changes a level to its output string."""
    if int(lvl) == 0:
        return "Evo"
    return lvl

def tm_mapper(_):
    return "yes"

def get_data(move):
    """Given a move name return the data for that move."""
    with open(CSV_DIR + move.strip().lower() + ".csv", 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        all_kinds = {}
        for row in reader:
            # id(ndex), kind, game(SpSc), level(0 for other kind), poke name
            if len(row) != 5:
                logging.error("csv row has the wrong number of items: " + str(len(row)))
                raise ValueError("csv row has the wrong number of items: " + str(len(row)))
            if row[2].strip() != "SpSc":
                logging.error("csv row has the wrong game: SpSc expected, " + row[2].strip() + " got")
                raise ValueError("csv row has the wrong game: SpSc expected, " + row[2].strip() + " got")

            ndex = get_ndex(row[0].strip(), row[4].strip())
            kind = row[1].strip()
            if kind not in all_kinds:
                all_kinds[kind] = {}
            if ndex not in all_kinds[kind]:
                all_kinds[kind][ndex] = []
            all_kinds[kind][ndex].append(row[3].strip())
    # Post processing
    for k, v in all_kinds["level"].items():
        all_kinds["level"][k] = list(map(level_mapper, sorted(v, key=level_sort_key)))
    for k, v in all_kinds["tm"].items():
        all_kinds["tm"][k] = list(map(tm_mapper, v))
    return all_kinds
