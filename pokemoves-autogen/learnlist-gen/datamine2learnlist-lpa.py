#!/usr/bin/python3
"""Parse LPA datamine and interactively produces learnlists."""

import re
import sys
import logging
import os
from typing import List, Tuple

logger = logging.getLogger("log")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

file_lh = logging.FileHandler("logs/" + os.path.basename(__file__) + ".log")
file_lh.setLevel(logging.DEBUG)
file_lh.setFormatter(formatter)
logger.addHandler(file_lh)

stdio_lh = logging.StreamHandler()
stdio_lh.setLevel(logging.WARNING)
stdio_lh.setFormatter(formatter)
logger.addHandler(stdio_lh)


class DatamineParser:
    REPLACES = {
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
        "gastrodon": "gastrodon",
        "cherrim": "cherrim",
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
        "growlithe-1": "growlitheH",
        "arcanine-1": "arcanineH",
        "voltorb-1": "voltorbH",
        "electrode-1": "electrodeH",
        "typhlosion-1": "typhlosionH",
        "qwilfish-1": "qwilfishH",
        "sneasel-1": "sneaselH",
        "wormadam-1": "wormadamSa",
        "wormadam-2": "wormadamSc",
        "dialga-1": "dialgaO",
        "palkia-1": "palkiaO",
        "shaymin-1": "shayminC",
        "samurott-1": "samurottH",
        "lilligant-1": "lilligantH",
        "basculin-2": "basculinH",
        "zorua-1": "zoruaH",
        "zoroark-1": "zoroarkH",
        "braviary-1": "braviaryH",
        "sliggoo-1": "sliggooH",
        "goodra-1": "goodraH",
        "avalugg-1": "avaluggH",
        "decidueye-1": "decidueyeH",
    }

    @staticmethod
    def normalize_pokename(poke):
        poke = poke.strip().lower().replace(" ", "-")
        if poke in DatamineParser.REPLACES:
            return DatamineParser.REPLACES[poke]
        else:
            return poke

    @staticmethod
    def split_moves(lines):
        """Return a Tuple[List[str], List[str]]
        These are lists of moves learned by level and tutor respectively
        """
        res = []
        for fline in ("Level:", "Move Shop:"):
            try:
                idx = lines.index(fline) + 1
                moves = []
                while idx < len(lines) and lines[idx].startswith("- "):
                    moves.append(lines[idx])
                    idx += 1
                res.append(moves)
            except ValueError:
                res.append([])
        # Reorder res to have the expected order
        return tuple(res)

    @staticmethod
    def level_tostr(lvl):
        lvl = int(lvl)
        if lvl == 0:
            return "Evo"
        if lvl == 1:
            return "Inizio"
        return str(lvl)

    @staticmethod
    def parse_move_line(line, kind):
        if kind == 0:  # level
            # - Confusione @ 0, mastered @ 15
            regex = "^- \[(\d{1,3})\] \[(\d{1,3})\] (.*)$"
        elif kind == 1:  # tutor
            regex = "^- (.*)$"

        m = re.match(regex, line.strip())
        if not m:
            logger.error("Line of kind {} doesn't match the regex".format(kind))
            logger.error(line)
            exit(1)

        res = m.groups()
        if kind == 0:
            res = (
                res[2],
                DatamineParser.level_tostr(res[0]),
                DatamineParser.level_tostr(res[1]),
            )
        return res

    @staticmethod
    def all_pokes_info(filename):
        res = {}
        with open(filename, "r") as f:
            pokelines = []
            move = ""
            for line in f:
                line = line.strip()
                if line == "":  # Empty lines are the separators
                    pokename = DatamineParser.normalize_pokename(pokelines[0])
                    if re.search("-\d+$", pokename):
                        pwb.warning(
                            '{} name ends in "-number". This may be caused by a missing replacement'.format(
                                pokename
                            )
                        )
                    # logger.info(pokename)

                    moves_by_kind = DatamineParser.split_moves(pokelines)
                    parsed_moves = [
                        [DatamineParser.parse_move_line(l, i) for l in lines]
                        for i, lines in enumerate(moves_by_kind)
                    ]
                    # logger.debug(str(list(parsed_moves)))
                    res[pokename] = parsed_moves
                    res[pokename.lower()] = parsed_moves
                    pokelines = []
                else:
                    pokelines.append(line)
        return res

    def __init__(self, filename):
        self.info = DatamineParser.all_pokes_info(filename)

    OUTPUT_LINES = (
        "|{}|||{}|{}| //",  # 0 -> level
        "|{}|||yes| //",  # 1 -> tutor
    )

    KIND_NAME = (
        "level",  # 0 -> level
        "tutor",  # 1 -> tutor
    )

    def get_learnlists(self, poke, kind):
        """Returns the learnlist call for the given input."""
        parsed_moves = self.info[poke.lower()][kind]
        kindname = DatamineParser.KIND_NAME[kind]
        res = ""
        res += "=====Forma di Hisui=====\n"
        res = (
            "{{{{#invoke: Learnlist/hf | {}hLPA | {} | 8 }}}}\n".format(kindname, poke)
            + "{{{{#invoke: render | render | Modulo:Learnlist/entry8LPA | {} | //\n".format(
                kindname
            )
            + "".join(
                map(
                    lambda move: DatamineParser.OUTPUT_LINES[kind].format(*move) + "\n",
                    parsed_moves,
                )
            )
            + "}}\n"
            + "{{{{#invoke: Learnlist/hf | {}fLPA | {} | 8 }}}}\n".format(
                kindname, poke
            )
        )
        return res


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: missing datamine file name. Aborting")
        exit(1)
    dmparsed = DatamineParser(sys.argv[1])
    print("Parsed succesfully, starting interactive mode")
    # Enter the interactive cycle: asks for a Pokémon, a kind and spits out the
    # corresponding learnlist
    while True:
        print("=========================================================")
        poke = input("Insert Pokémon name: ").strip()
        kind = int(input("Insert kind (0 = level, 1 = tutor): "))
        print()
        try:
            learnlist = dmparsed.get_learnlists(poke, kind)
            print(learnlist)
        except:
            print("Something went wrong: try again")
