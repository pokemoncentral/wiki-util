#!/usr/bin/python3

import sys
from typing import Callable, Literal

from datamine_parser import Game, Pkmn, parse_pkmn

LuaModule = Literal["poke-data", "poke-stats", "poke-abils"]

extractors: dict[LuaModule, Callable[[Pkmn], str]] = {
    "poke-data": Pkmn.to_poke_data,
    "poke-abils": Pkmn.to_poke_abil_data,
    "poke-stats": Pkmn.to_poke_stats,
}


def main(game: Game, lua_module: LuaModule, datamine_file: str):
    parser = parse_pkmn(game)
    extractor = extractors[lua_module]

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
