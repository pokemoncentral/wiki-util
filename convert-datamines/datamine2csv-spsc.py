#!/usr/bin/python3
import re
import csv
import sys
import logging
from typing import List, Tuple

logger = logging.getLogger("log")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_lh = logging.FileHandler("logs/datamine2csv.log")
file_lh.setLevel(logging.DEBUG)
file_lh.setFormatter(formatter)
logger.addHandler(file_lh)

stdio_lh = logging.StreamHandler()
stdio_lh.setLevel(logging.WARNING)
stdio_lh.setFormatter(formatter)
logger.addHandler(stdio_lh)

replaces = {
    "mr.-mime": "mr. mime",
    "mr.-mime-1": "mr. mimeG",
    "mime-jr.": "mime jr.",
    "mr.-rime": "mr. rime",
    "pikachu": "pikachu",
    "pikachu-1": "pikachuO",
    "pikachu-2": "pikachuH",
    "pikachu-3": "pikachuSi",
    "pikachu-4": "pikachuU",
    "pikachu-5": "pikachuK",
    "pikachu-6": "pikachuA",
    "pikachu-7": "pikachuCo",
    "raichu": "raichu",
    "raichu-1": "raichuA",
    "darumaka": "darumaka",
    "darumaka-1": "darumakaG",
    "darmanitan": "darmanitan",
    "darmanitan-1": "darmanitanZ",
    "darmanitan-2": "darmanitanG",
    "darmanitan-3": "darmanitanGZ",
    "vulpix": "vulpix",
    "vulpix-1": "vulpixA",
    "ninetales": "ninetales",
    "ninetales-1": "ninetalesA",
    "diglett": "diglett",
    "diglett-1": "diglettA",
    "dugtrio": "dugtrio",
    "dugtrio-1": "dugtrioA",
    "meowth": "meowth",
    "meowth-1": "meowthA",
    "meowth-2": "meowthG",
    "persian": "persian",
    "persian-1": "persianA",
    "ponyta": "ponyta",
    "ponyta-1": "ponytaG",
    "rapidash": "rapidash",
    "rapidash-1": "rapidashG",
    "weezing": "weezing",
    "weezing-1": "weezingG",
    "corsola": "corsola",
    "corsola-1": "corsolaG",
    "zigzagoon": "zigzagoon",
    "zigzagoon-1": "zigzagoonG",
    "linoone": "linoone",
    "linoone-1": "linooneG",
    "stunfisk": "stunfisk",
    "stunfisk-1": "stunfiskG",
    "farfetch'd": "farfetchd",
    "farfetch’d": "farfetchd",
    "farfetch'd-1": "farfetchdG",
    "farfetch’d-1": "farfetchdG",
    "sirfetch'd": "sirfetchd",
    "sirfetch’d": "sirfetchd",
    "cramorant": "cramorant",
    "cramorant-1": "cramorantT",
    "cramorant-2": "cramorantI",
    "toxtricity": "toxtricity",
    "toxtricity-1": "toxtricityB",
    "eiscue": "eiscue",
    "eiscue-1": "eiscueL",
    "indeedee": "indeedee",
    "indeedee-1": "indeedeeF",
    "morpeko": "morpeko",
    "morpeko-1": "morpekoV",
    "zacian": "zacian",
    "zacian-1": "zacianR",
    "zamazenta": "zamazenta",
    "zamazenta-1": "zamazentaR",
    "eternatus": "eternatus",
    "eternatus-1": "eternatusD",
    "shellos": "shellos",
    "shellos-1": "shellosE",
    "gastrodon": "gastrodon",
    "gastrodon-1": "gastrodonE",
    "cherrim": "cherrim",
    "cherrim-1": "cherrimS",
    "sinistea": "sinistea",
    "sinistea-1": "sinisteaA",
    "polteageist": "polteageist",
    "polteageist-1": "polteageistA",
    "alcremie": "alcremie",
    "alcremie-1": "alcremieR",
    "alcremie-2": "alcremieMa",
    "alcremie-3": "alcremieMe",
    "alcremie-4": "alcremieL",
    "alcremie-5": "alcremieS",
    "alcremie-6": "alcremieRm",
    "alcremie-7": "alcremieCm",
    "alcremie-8": "alcremieTm",
    "mimikyu": "mimikyu",
    "mimikyu-1": "mimikyuS",
    "silvally": "silvally",  # TODO silvally
    "silvally-1": "silvally",
    "silvally-2": "silvally",
    "silvally-3": "silvally",
    "silvally-4": "silvally",
    "silvally-5": "silvally",
    "silvally-6": "silvally",
    "silvally-7": "silvally",
    "silvally-8": "silvally",
    "silvally-9": "silvally",
    "silvally-10": "silvally",
    "silvally-11": "silvally",
    "silvally-12": "silvally",
    "silvally-13": "silvally",
    "silvally-14": "silvally",
    "silvally-15": "silvally",
    "silvally-16": "silvally",
    "silvally-17": "silvally",
    "type:null": "tipo zero",
    "type:-null": "tipo zero",
    "necrozma": "necrozma",
    "necrozma-1": "necrozmaV",
    "necrozma-2": "necrozmaA",
    "wishiwashi": "wishiwashi",
    "wishiwashi-1": "wishiwashiB",
    "pumpkaboo": "pumpkaboo",
    "pumpkaboo-1": "pumpkabooS",
    "pumpkaboo-2": "pumpkabooL",
    "pumpkaboo-3": "pumpkabooXL",
    "gourgeist": "gourgeist",
    "gourgeist-1": "gourgeistS",
    "gourgeist-2": "gourgeistL",
    "gourgeist-3": "gourgeistXL",
    "aegislash": "aegislash",
    "aegislash-1": "aegislashS",
    "meowstic": "meowstic",
    "meowstic-1": "meowsticF",
    "keldeo": "keldeo",
    "keldeo-1": "keldeoR",
    "kyurem": "kyurem",
    "kyurem-1": "kyuremN",
    "kyurem-2": "kyuremB",
    "yamask": "yamask",
    "yamask-1": "yamaskG",
    "basculin": "basculin",
    "basculin-1": "basculinB",
    "rotom": "rotom",
    "rotom-1": "rotomC",
    "rotom-2": "rotomL",
    "rotom-3": "rotomG",
    "rotom-4": "rotomV",
    "rotom-5": "rotomT",
    "exeggutor-1": "exeggutorA",
    "marowak-1": "marowakA",
    "sandshrew-1": "sandshrewA",
    "sandslash-1": "sandslashA",
    "slowpoke-1": "slowpokeG",
    "slowbro-2": "slowbroG",
    "slowking-1": "slowkingG",
    "lycanroc": "lycanroc",
    "lycanroc-1": "lycanrocN",
    "lycanroc-2": "lycanrocC",
    "urshifu-1": "urshifuP",
    "articuno-1": "articunoG",
    "zapdos-1": "zapdosG",
    "moltres-1": "moltresG",
    "calyrex-1": "calyrexG",
    "calyrex-2": "calyrexS",
    "giratina-1": "giratinaO",
    "tornadus-1": "tornadusT",
    "thundurus-1": "thundurusT",
    "landorus-1": "landorusT",
    "zygarde-1": "zygardeD",
    "zygarde-4": "zygardeP",
    "tapu-koko": "tapu koko",
    "tapu-lele": "tapu lele",
    "tapu-bulu": "tapu bulu",
    "tapu-fini": "tapu fini",
    "zarude-1": "zarudeP",
}


def convert_pokename(poke: str):
    poke = poke.lower().replace(" ", "-")
    if poke in replaces:
        return replaces[poke]
    else:
        return poke


def get_move_id(move: str):
    move = move.strip().lower()
    # 1,botta,1,1,40,35,100,0,10,2,1,,5,1,5
    with open("docker-db/sourcecsv/moves.csv", "r") as movesfile:
        moves = csv.reader(movesfile)
        next(moves)
        for line in moves:
            if line[1].strip().lower() == move:
                return line[0]


def get_poke_id(poke: str):
    poke = poke.strip().lower()
    # 1,botta,1,1,40,35,100,0,10,2,1,,5,1,5
    with open("docker-db/sourcecsv/pokemon.csv", "r") as file:
        r = csv.reader(file)
        next(r)
        for line in r:
            if line[1].strip().lower() == poke:
                return line[0]


def split_moves(lines: List[str]):
    """Return a Tuple[List[str], List[str], List[str], List[str]]
    These are lists of moves learned by level, breed, tm and tutor
    """
    res = []
    for fline in ("Level Up Moves:", "Egg Moves:", "TMs:", "TRs:", "Armor Tutors:"):
        try:
            idx = pokelines.index(fline) + 1
            moves = []
            while pokelines[idx].startswith("- "):
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
        # breed
        regex = "^\- (.*)$"
    elif kind == 2:
        # tm
        regex = "^\- \[TM\d{1,3}\] (.*)$"
    elif kind == 3:
        # tr
        regex = "^\- \[TR\d{1,3}\] (.*)$"
    elif kind == 4:
        # tutor
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
    """
    if kind == 0:
        return 1
    elif kind == 1:
        return 2
    elif kind == 2:
        return 4
    elif kind == 3:
        return 4
    elif kind == 4:
        return 3


def write_row_csv_pokemoves(poke_id: str, kind: int, elem: Tuple, csvw):
    if kind == 0:
        move = elem[1]
        level = elem[0]
    else:
        move = elem[0]
        level = 0
    move_id = get_move_id(move)
    if not move_id:
        logging.error("No ID for move " + move)
        exit(1)
    # pokemon_id,version_group_id,move_id,pokemon_move_method_id,level,order
    version_group_id = 19
    if kind == 4:
        # tutor
        version_group_id = 20
    csvw.writerow([poke_id, version_group_id, move_id, convert_kind(kind), level, 0])


with open(sys.argv[1], "r") as f, open(sys.argv[2], "w") as out:
    csvw = csv.writer(out)
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
                pokename = convert_pokename(m.group(1))
                poke_id = get_poke_id(pokename)
                if not poke_id:
                    logger.error("No ID for Pokémon " + pokename)
                    exit(1)
                logger.info(pokename)
            else:
                moves_by_kind = split_moves(pokelines)
                # logger.debug(str(moves_by_kind))
                parsed_moves = (
                    list(map(lambda l: parse_move_line(l, i), lines))
                    for i, lines in enumerate(moves_by_kind)
                )
                # logger.debug(str(parsed_moves))
                for kind, moves in enumerate(parsed_moves):
                    for move in moves:
                        write_row_csv_pokemoves(poke_id, kind, move, csvw)
                pokelines = []
                pokename = False
        else:
            pokelines.append(line)
