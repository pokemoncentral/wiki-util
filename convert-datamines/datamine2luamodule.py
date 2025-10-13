#!/usr/bin/python3

import sys
from typing import Literal

from datamine_parser import Game, Pkmn, get_learnlist_serializer, get_pkmn_parser

LuaModule = Literal["poke-data", "poke-stats", "poke-abils", "learnlist"]


def main(game: Game, lua_module: LuaModule, datamine_file: str):
    parser = get_pkmn_parser(game)
    match lua_module:
        case "poke-data":
            extractor = Pkmn.to_poke_data

        case "poke-abils":
            extractor = Pkmn.to_poke_abil_data

        case "poke-stats":
            extractor = Pkmn.to_poke_stats

        case "learnlist":
            serializer = get_learnlist_serializer(game)
            extractor = lambda pkmn: serializer(pkmn.moves)

    with open(datamine_file, "r", encoding="utf-8") as f:
        datamine_lines = map(str.strip, f.readlines())

        try:
            while True:
                pkmn = parser(datamine_lines)
                if pkmn is not None:
                    print(extractor(pkmn))
        except StopIteration:
            pass


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
