#!/usr/bin/python3
import re
import csv
import sys
import logging
from typing import List, Tuple
from lib import convert_pokename, get_move_id, get_poke_id, should_ignore

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


def split_moves(lines: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Return lists of moves learned by level, tm, breed, reminder."""
    res = []
    for fline in ("Level Up Moves:", "TM Learn:", "Egg Moves:", "Reminder:"):
        try:
            idx = pokelines.index(fline) + 1
            moves = []
            while idx < len(pokelines) and pokelines[idx].startswith("- "):
                moves.append(pokelines[idx])
                idx += 1
            res.append(moves)
        except ValueError:
            res.append([])
    return tuple(res)


def parse_move_line(line: str, kind: int):
    if kind == 0:
        # level
        regex = "^\- \[(\d{1,3})\] (.*)$"
    elif kind == 1:
        # tm
        regex = "^\- \[TM\d{1,3}\] (.*)$"
    elif kind == 2 or kind == 3:
        # breed, reminder
        regex = "^\- (.*)$"

    m = re.match(regex, line)
    if not m:
        logger.error("Line of kind " + str(kind) + " doesn't match the regex")
        logger.error(line)
        exit(1)
    return m.groups()


def convert_kind(kind: int):
    """
    1,level
    2,breed
    3,tutor
    4,tm
    11,reminder
    """
    if kind == 0:
        return 1
    elif kind == 1:
        return 4
    elif kind == 2:
        return 2
    elif kind == 3:
        return 11


def write_row_csv_pokemoves(poke_id: str, kind: int, elem: Tuple, csvw):
    if kind == 0:
        move = elem[1]
        level = str(int(elem[0]))
    else:
        move = elem[0]
        level = 0
    move_id = get_move_id(move)
    if not move_id:
        logging.error("No ID for move " + move)
        exit(1)
    # pokemon_id,version_group_id,move_id,pokemon_move_method_id,level,order
    version_group_id = 24
    csvw.writerow([poke_id, version_group_id, move_id, convert_kind(kind), level, 0])


with open(sys.argv[1], "r") as f, open(sys.argv[2], "w", newline="") as out:
    csvw = csv.writer(out, lineterminator="\n")
    pokelines = []
    pokename = False
    move = ""
    for line in f:
        line = line.strip()
        if line == "======":
            if not pokename:
                if not len(pokelines) == 1:
                    logger.error("More than one line when expecting the Pokémon name")
                    exit(1)
                m = re.match("\d{3,4} \- (.*) \(Stage\: \d\)", pokelines[0])
                if not m:
                    logger.error("Pokémon name line doesn't match the regex")
                    logger.error(pokelines[0])
                    exit(1)
                pokename = m.group(1)
                pokename = re.sub("(K)?#\d{3}", "", pokename).strip()
                pokename = convert_pokename(pokename)
                if not should_ignore(pokename):
                    # Ignore a bunch of forms
                    poke_id = get_poke_id(pokename)
                    if not poke_id:
                        logger.error("No ID for Pokémon " + pokename)
                        exit(1)
                    logger.info(f"{pokename} ({poke_id})")
                    continue
            else:
                if not should_ignore(pokename):
                    logger.debug(f"Number of lines: {len(pokelines)}")
                    moves_by_kind = split_moves(pokelines)
                    parsed_moves = (
                        list(map(lambda l: parse_move_line(l, i), lines))
                        for i, lines in enumerate(moves_by_kind)
                    )
                    for kind, moves in enumerate(parsed_moves):
                        for move in moves:
                            write_row_csv_pokemoves(poke_id, kind, move, csvw)
                pokelines = []
                pokename = False
        else:
            pokelines.append(line)
