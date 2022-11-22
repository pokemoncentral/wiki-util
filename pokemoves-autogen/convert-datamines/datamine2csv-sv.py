#!/usr/bin/python3
import re
import csv
import sys
import logging
from typing import List, Tuple
from lib import replaces, should_ignore

logger = logging.getLogger("log")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_lh = logging.FileHandler("logs/" + sys.argv[0] + ".log")
file_lh.setLevel(logging.DEBUG)
file_lh.setFormatter(formatter)
logger.addHandler(file_lh)

stdio_lh = logging.StreamHandler()
stdio_lh.setLevel(logging.WARNING)
stdio_lh.setFormatter(formatter)
logger.addHandler(stdio_lh)


def flatten(l):
    return [item for sublist in l for item in sublist]


def convert_pokename(poke: str):
    poke = poke.lower().replace(" ", "-")
    if poke in replaces:
        return replaces[poke]
    else:
        return poke


def get_move_id(move: str):
    move = move.strip().lower()
    with open("docker-db/sourcecsv/moves.csv", "r") as movesfile:
        moves = csv.reader(movesfile)
        next(moves)
        for line in moves:
            if line[1].strip().lower() == move:
                return line[0]


def get_poke_id(poke: str):
    poke = poke.strip().lower()
    with open("docker-db/sourcecsv/pokemon.csv", "r") as file:
        r = csv.reader(file)
        next(r)
        for line in r:
            if line[1].strip().lower() == poke:
                return line[0]


def split_moves(lines: List[str]):
    """Return a Tuple[List[str], List[str], List[str], List[str]]
    These are lists of moves learned by level, breed, tm and reminder
    """
    res = []
    flines = ("Learned Moves:", "Egg Moves:", "TM Moves:", "Reminder Moves:")
    for fline in flines:
        try:
            idx = pokelines.index(fline) + 1
            moves = []
            while idx < len(pokelines) and (pokelines[idx] not in flines):
                moves.append(pokelines[idx])
                idx += 1
            res.append(moves)
        except ValueError:
            res.append([])
    return tuple(res)


def parse_move_line(line: str, kind: int):
    if kind == 0:
        # level
        m = re.match("^(.+) @ Lv. (\d{1,3})$", line)
        if not m:
            m = re.match("^(.+) @ Evolution$", line)
            if not m:
                logger.error("Level line doesn't match the regex")
                logger.error(line)
                exit(1)
            return (m.group(1), 0)
        return m.groups()
    elif kind == 1 or kind == 2 or kind == 3:
        # breed or tm or reminder
        return line.split(", ")


def prepare_parsed_moves(parsed_moves):
    return (
        parsed_moves[0],
        flatten(parsed_moves[1]),
        flatten(parsed_moves[2]),
        flatten(parsed_moves[3]),
    )


def convert_kind(kind: int):
    """
    1,level
    2,breed
    3,tutor
    4,tm
    """
    if kind == 0:
        return 1
    elif kind == 1:
        return 2
    elif kind == 2:
        return 4
    elif kind == 3:
        return 1


def write_row_csv_pokemoves(poke_id: str, kind: int, elem: Tuple, csvw):
    if kind == 0:
        move = elem[0]
        level = elem[1]
    elif kind == 3:
        move = elem
        level = 1
    else:
        move = elem
        level = 0
    move_id = get_move_id(move)
    if not move_id:
        logging.error("No ID for move " + move)
        exit(1)
    version_group_id = 23
    # pokemon_id,version_group_id,move_id,pokemon_move_method_id,level,order
    csvw.writerow([poke_id, version_group_id, move_id, convert_kind(kind), level, 0])


with open(sys.argv[1], "r") as f, open(sys.argv[2], "w") as out:
    csvw = csv.writer(out, lineterminator="\n")
    pokelines = []
    move = ""
    for line in f:
        line = line.strip()
        if line == "":  # Empty lines are the separators
            try:
                pokename = pokelines[0].split(" - ")[0].strip()
            except IndexError:
                logger.error("Can't find Pokémon name")
                logger.error(lines[0])
                exit(1)
            pokename = convert_pokename(pokename)
            if should_ignore(pokename):
                # Ignore a bunch of forms
                pokelines = []
                continue
            poke_id = get_poke_id(pokename)
            if not poke_id:
                logger.error("No ID for Pokémon " + pokename)
                exit(1)
            logger.info(pokename)

            moves_by_kind = split_moves(pokelines)
            logger.debug(str(moves_by_kind))
            parsed_moves = [
                [parse_move_line(l, i) for l in lines]
                for i, lines in enumerate(moves_by_kind)
            ]
            parsed_moves = prepare_parsed_moves(parsed_moves)
            logger.debug(str(parsed_moves))
            for kind, moves in enumerate(parsed_moves):
                for move in moves:
                    write_row_csv_pokemoves(poke_id, kind, move, csvw)

            pokelines = []
        else:
            pokelines.append(line)
