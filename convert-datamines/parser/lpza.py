import re
from itertools import chain, cycle, islice
from typing import Generator, Literal, Optional, Tuple

from dtos import Abilities, Moves, Pkmn, Stats
from Learnlist import LearnLevel, parse_learnlevel
from lib import find

LuaModule = Literal["poke-data", "poke-stats", "poke-abils", "learnlist"]

LpzaLevelUpMove = Tuple[LearnLevel, int, str]


def parse(datamine_file: str) -> Generator[Pkmn]:
    with open(datamine_file, "r", encoding="utf-8") as f:
        datamine_lines = map(str.strip, f)
        try:
            while True:
                pkmn = parse_pkmn(datamine_lines)
                if pkmn is not None:
                    yield pkmn
        except StopIteration:
            pass


def extract_ability(abilities: list[str], tag: str) -> str:
    tag = f"({tag})"
    ability = find(abilities, lambda a: a.endswith(tag))
    return normalize(ability.replace(tag, "").strip())


def is_move_list_item(line: str) -> bool:
    return line.startswith("- ")


def parse_pkmn(datamine_lines: Generator[str]) -> Optional[Pkmn]:
    while True:
        line = next(datamine_lines)

        if "(Stage: " in line:
            ndex, _, name_and_rest = line.partition(" - ")
            ndex = int(ndex.strip())
            name = parse_name(name_and_rest)

        elif line.startswith("Base Stats"):
            stats = parse_stats(line)

        elif line.startswith("Abilities"):
            abilities = parse_abilities(line)

        elif line.startswith("Type"):
            types = parse_types(line)

        elif line.startswith("Alpha Move"):
            moves = parse_moves(chain((line,), datamine_lines))
            break

    return Pkmn.create(
        ndex=ndex,
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
    level_up, tm, egg, reminder, alpha = [], [], [], [], []
    current_move_list, current_move_parser = None, None
    for line in datamine_lines:
        if is_move_list_item(line):
            current_move_list.append(current_move_parser(line))
            continue

        match line:
            case "Level Up Moves:":
                current_move_list, current_move_parser = level_up, parse_move_level_up

            case "TM Learn:":
                current_move_list, current_move_parser = tm, parse_move_tm

            case "Egg Moves:":
                current_move_list, current_move_parser = egg, parse_move_prefixed

            case "Reminder:":
                current_move_list, current_move_parser = reminder, parse_move_prefixed

            case _ if line.startswith("Alpha Move:"):
                alpha.append(line.partition(":")[2].strip())

            case "":
                break

            case _ if line.startswith("Evolves"):
                break

            case _:
                raise ValueError(f"Unknown move heading: {line}")

    return Moves[LpzaLevelUpMove](level_up, tm, egg, reminder, alpha)


level_up_regex = re.compile(r"- \[(-?\d{1,3})\] (.+?) \{(\d{1,3})\}")


def parse_move_level_up(level_up_line: str) -> LpzaLevelUpMove:
    [level, name, plus_level] = level_up_regex.match(level_up_line).groups()
    return (parse_learnlevel(int(level)), int(plus_level), normalize(name.strip()))


def parse_move_tm(tm_line: str) -> Tuple[str, str]:
    [_, tm, *name] = tm_line.split(" ")
    return ("MT" + tm[3:-1], normalize(" ".join(name)))


def parse_move_prefixed(line: str) -> str:
    return normalize(line.removeprefix(" -"))


def parse_name(name_segment: str) -> str:
    name_end = min(name_segment.find("#"), name_segment.find("("))
    name = name_segment if name_end == -1 else name_segment[:name_end]
    return normalize(name.strip())


def parse_stats(line: str) -> Stats:
    numbers, *_ = line.removeprefix("Base Stats: ").partition(" ")
    return Stats(*map(int, numbers.split(".")))


def parse_types(line: str) -> Tuple[str, str]:
    types = line.removeprefix("Type: ").split(" / ")
    return tuple(islice(cycle(types), 2))


def normalize(text: str) -> str:
    return text.replace("’", "'")
