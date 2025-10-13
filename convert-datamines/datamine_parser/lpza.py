from itertools import cycle, dropwhile, islice
from typing import Generator, Optional, Tuple

from lib import find

from .dtos import Abilities, Moves, Pkmn, Stats


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


def parse_move_level_up(level_up_line: str) -> Tuple[int, str]:
    [_, level, *name] = level_up_line.split(" ")
    return (int(level[1:-1]), " ".join(name))


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


def serialize_learnlist(moves: Moves) -> str:
    level_up = (
        """
{{#invoke: Learnlist/hf | levelhLZPA | 9 }}
{{#invoke: render | render | Modulo:Learnlist/entry9LZPA | level | //
"""
        + "\n".join(
            f"|{name}|||{level}|{{other}}| //" for level, name in moves.level_up
        )
        + """
}}
{{#invoke: Learnlist/hf | levelfLZPA | 9 }}
"""
    )

    tutor = (
        """
{{#invoke: Learnlist/hf | tutorhLZPA | Vespiquen | 9 }}
{{#invoke: render | render | Modulo:Learnlist/entry9LPZA | tutor | //
"""
        + "\n".join(f"|{name}|||yes| //" for name in moves.reminder)
        + """
}}
{{#invoke: Learnlist/hf | tutorfLPA | 9 }}
"""
    )

    return level_up + tutor
