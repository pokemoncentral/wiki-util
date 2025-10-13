from typing import Callable, Generator, Literal, Optional

from . import dtos, lpza

Game = Literal["lpza"]
Pkmn = dtos.Pkmn


def get_pkmn_parser(game: Game) -> Callable[[Generator[str]], Optional[dtos.Pkmn]]:
    match game:
        case "lpza":
            return lpza.parse_pkmn


def get_learnlist_serializer(game: Game) -> Callable[[dtos.Moves], str]:
    match game:
        case "lpza":
            return lpza.serialize_learnlist
