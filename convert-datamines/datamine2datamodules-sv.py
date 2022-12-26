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

file_lh = logging.FileHandler("logs/datamine2datamodules.log")
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


def normalize_type(t: str):
    t = t.lower()
    if t == "psichico":
        return "psico"
    if t == "coleottero":
        return "coleot"
    return t


def get_types(line: str):
    # Fuoco/Roccia
    types = line.split("/")
    if len(types) != 2:
        logging.error("Two types expected")
        logging.error(line)
        exit(1)
    # Fucking coleot
    if types[0] == types[1] and types[1] == "Coleottero":
        return ("coleottero", "coleottero")
    return (normalize_type(types[0]), normalize_type(types[1]))


def get_abils(line: str):
    # Prepotenza/Fuocardore/Testadura
    abils = [l.strip() for l in line.split("/")]
    if len(abils) != 3:
        logging.error("Three abils expected")
        logging.error(line)
        exit(1)
    return abils


def get_stats(line: str):
    # 60/75/45/65/50/55 (Total: 350)
    m = re.fullmatch("(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/(\d+) \(Total: \d+\)", line)
    if not m:
        logging.error("Wrong format for stats block")
        logging.error(line)
        exit(1)
    return [int(m.group(i)) for i in range(1, 7)]


def get_data(header: str):
    # Growlithe-1 - 60/75/45/65/50/55 (Total: 350) - Fuoco/Roccia - Prepotenza/Fuocardore/Testadura
    blocks = [s.strip() for s in header.split(" - ")]
    return {
        "types": get_types(blocks[2]),
        "abils": get_abils(blocks[3]),
        "stats": get_stats(blocks[1]),
    }


def get_evodata(lines: List[str]):
    logger.debug("Ha le evo")
    logger.debug(lines[-1])
    return {}


def print_pokedata(name: str, truename: str, data: Tuple[str, str]):
    # t.skeledirge = {name = 'Skeledirge', ndex = 911, type1 = 'fuoco', type2 = 'spettro'}
    if not re.fullmatch("\w+", name):
        begin = 't["{name}"]'.format(name=name)
    else:
        begin = "t." + name
    return "{begin} = {{name = '{truename}', ndex = nil, type1 = '{type1}', type2 = '{type2}' }}".format(
        begin=begin, truename=truename, type1=data[0], type2=data[1]
    )


def print_pokeabildata(name: str, data: List[str]):
    # t.taurosC = {ability1 = 'Prepotenza', ability2 = 'Grancollera', abilityd = 'Cud Chew'}
    if not re.fullmatch("\w+", name):
        begin = 't["{name}"]'.format(name=name)
    else:
        begin = "t." + name
    result = begin + " = {{ability1 = '{abil1}'".format(abil1=data[0])
    if data[1] != data[0]:
        result += ", ability2 = '{abil2}'".format(abil2=data[1])
    if data[2] != data[0]:
        result += ", abilityd = '{abild}'".format(abild=data[2])
    return result + "}"


def print_pokestatsdata(name: str, data: List[int]):
    # d.grandizanne = {hp = 115, atk = 131, def = 131, spatk = 53, spdef = 53, spe = 87}
    if not re.fullmatch("\w+", name):
        begin = 't["{name}"]'.format(name=name)
    else:
        begin = "t." + name
    data = list(map(int, data))
    stats = "{{hp = {hp}, atk = {atk}, def = {dif}, spatk = {spatk}, spdef = {spdef}, spe = {spe}}}".format(
        hp=data[0], atk=data[1], dif=data[2], spatk=data[3], spdef=data[4], spe=data[5]
    )
    return begin + " = " + stats


with open(sys.argv[1], "r") as f, open(sys.argv[2], "w") as out:
    csvw = csv.writer(out)
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
            normalized_name = convert_pokename(pokename)
            logger.debug(normalized_name)
            if should_ignore(normalized_name):
                # Ignore a bunch of forms
                pokelines = []
                continue

            # Extract data from the first line
            poke_data = get_data(pokelines[0])
            logger.debug(poke_data)
            # Get evolutions, if any
            if pokelines[1] == "Evolutions:":
                evodata = get_evodata(pokelines[2 : pokelines.index("Learned Moves:")])

            out.write(pokename + "\n")
            # out.write(print_pokedata(normalized_name, pokename, poke_data["types"]) + "\n")
            # out.write(print_pokeabildata(normalized_name, poke_data["abils"]) + "\n")
            # out.write(print_pokestatsdata(normalized_name, poke_data["stats"]) + "\n")

            pokelines = []
        else:
            pokelines.append(line)
