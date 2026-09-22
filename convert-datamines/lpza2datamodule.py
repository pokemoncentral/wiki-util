#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from parser.lpza import parse
from typing import Callable, Literal

from dtos import Pkmn

LuaModule = Literal["poke-data", "poke-stats", "poke-abils"]
serializers: dict[LuaModule, Callable[[Pkmn], str]] = {
    "poke-data": Pkmn.to_poke_data,
    "poke-abils": Pkmn.to_poke_abil_data,
    "poke-stats": Pkmn.to_poke_stats,
}


def main(lua_module: LuaModule, datamine_file: str):
    serializer = serializers[lua_module]
    for pkmn in parse(datamine_file):
        print(serializer(pkmn))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
