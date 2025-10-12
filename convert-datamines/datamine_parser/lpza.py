from itertools import cycle, dropwhile, islice
from typing import Generator, Optional, Tuple

from lib import find

from .dtos import Abilities, Pkmn, Stats


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

    return Pkmn.create(
        ndex=int(ndex.strip()),
        name=name,
        types=types,
        stats=stats,
        abilities=abilities,
    )


def parse_abilities(line: str) -> Abilities:
    abilities = line.removeprefix("Abilities: ").split(" | ")
    return Abilities(
        ability1=extract_ability(abilities, "1"),
        ability2=extract_ability(abilities, "2"),
        hidden_ability=extract_ability(abilities, "H"),
    )


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


def extract_ability(abilities: list[str], tag: str) -> str:
    tag = f"({tag})"
    ability = find(abilities, lambda a: a.endswith(tag))
    return ability.replace(tag, "").strip()
