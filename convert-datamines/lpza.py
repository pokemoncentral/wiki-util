#!/usr/bin/env python


import re
import sys
from itertools import cycle, dropwhile, islice
from typing import Any, Callable, Generator, Literal, Optional, Tuple

from dtos import Abilities, Moves, Pkmn, Stats
from lib import find

LuaModule = Literal["poke-data", "poke-stats", "poke-abils", "learnlist"]


def extract_ability(abilities: list[str], tag: str) -> str:
    tag = f"({tag})"
    ability = find(abilities, lambda a: a.endswith(tag))
    return ability.replace(tag, "").strip()


def is_move_list_item(line: str) -> bool:
    return line.startswith("- ")


def parse_pkmn(datamine_lines: Generator[str]) -> Optional[Pkmn]:
    next(dropwhile(lambda l: l != "======", datamine_lines))

    ndex_and_name_line = next(datamine_lines)
    ndex, _, name_and_rest = ndex_and_name_line.partition(" - ")
    name = parse_name(name_and_rest)

    stats = parse_stats(find(datamine_lines, lambda l: l.startswith("Base Stats")))
    abilities = parse_abilities(
        find(datamine_lines, lambda l: l.startswith("Abilities"))
    )

    types = parse_types(find(datamine_lines, lambda l: l.startswith("Type")))
    next(dropwhile(lambda l: l != "Level Up Moves:", datamine_lines))
    moves = parse_moves(datamine_lines)

    return Pkmn.create(
        ndex=int(ndex.strip()),
        name=name,
        types=types,
        stats=stats,
        abilities=abilities,
        moves=moves,
    )


def parse_abilities(line: str) -> Abilities:
    abilities = line.removeprefix("Abilities: ").split(" | ")
    return Abilities(
        ability1=extract_ability(abilities, "1"),
        ability2=extract_ability(abilities, "2"),
        hidden_ability=extract_ability(abilities, "H"),
    )


def parse_moves(datamine_lines: Generator[str]) -> Moves:
    level_up, tm, egg, reminder = [], [], [], []
    current_move_list, current_move_parser = level_up, parse_move_level_up
    for line in datamine_lines:
        if is_move_list_item(line):
            current_move_list.append(current_move_parser(line))
            continue

        match line:
            case "TM Learn:":
                current_move_list, current_move_parser = (tm, parse_move_tm)

            case "Egg Moves:":
                current_move_list, current_move_parser = (egg, parse_move_prefixed)

            case "Reminder:":
                current_move_list, current_move_parser = (reminder, parse_move_prefixed)

            case "":
                break

            case _ if line.startswith("Evolves"):
                break

            case _:
                raise ValueError(f"Unknown move heading: {line}")

    return Moves(level_up, tm, egg, reminder)


level_up_regex = re.compile(r"- \[(-?\d{1,3})\] (.+?) \{(\d{1,3})\}")


def parse_move_level_up(level_up_line: str) -> Tuple[Moves.Level, int, str]:
    [level, name, plus_level] = level_up_regex.match(level_up_line).groups()
    return (Moves.translate_int_level(int(level)), int(plus_level), name.strip())


def parse_move_tm(tm_line: str) -> Tuple[str, str]:
    [_, tm, *name] = tm_line.split(" ")
    return (tm[1:-1], " ".join(name))


def parse_move_prefixed(line: str) -> str:
    return line.removeprefix(" -")


def parse_name(name_segment: str) -> str:
    name_end = min(name_segment.find("#"), name_segment.find("("))
    name = name_segment if name_end == -1 else name_segment[:name_end]
    return name.strip()


def parse_stats(line: str) -> Stats:
    numbers, *_ = line.removeprefix("Base Stats: ").partition(" ")
    return Stats(*map(int, numbers.split(".")))


def parse_types(line: str) -> Tuple[str, str]:
    types = line.removeprefix("Type: ").split(" / ")
    return tuple(islice(cycle(types), 2))


def serialize_learnlist(pkmn: Pkmn) -> Tuple[str, str]:
    return (
        f"""
{{{{#invoke: Learnlist-LPZA | level | {pkmn.name} | //
{"\n".join(        f"| {level} | {plus_level} | {name} | //"
        for level, plus_level, name in pkmn.moves.level_up
)}
}}}}
""".strip(),
        f"""
{{{{#invoke: Learnlist-LPZA | tm | {pkmn.name} | //
{"\n".join(f"| {tm} | {name} | //" for tm, name in pkmn.moves.tm)}
}}}}
""".strip(),
    )


def map_datamine(
    lua_module: LuaModule, datamine_file: str
) -> Generator[Tuple[Pkmn, Any]]:
    match lua_module:
        case "poke-data":
            serializer = Pkmn.to_poke_data

        case "poke-abils":
            serializer = Pkmn.to_poke_abil_data

        case "poke-stats":
            serializer = Pkmn.to_poke_stats

        case "learnlist":
            serializer = serialize_learnlist

    with open(datamine_file, "r", encoding="utf-8") as f:
        datamine_lines = map(str.strip, f.readlines())

        try:
            while True:
                pkmn = parse_pkmn(datamine_lines)
                if pkmn is not None:
                    yield (pkmn, serializer(pkmn))
        except StopIteration:
            pass


def main(lua_module: LuaModule, datamine_file: str):
    for _, output in map_datamine(lua_module, datamine_file):
        output = "\n".join(output) if isinstance(output, tuple) else output
        print(output)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
