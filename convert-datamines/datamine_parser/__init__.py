from typing import Callable, Generator, Literal, Optional

from . import dtos, lpza

Game = Literal["lpza"]
Pkmn = dtos.Pkmn


def parse_pkmn(
    parser: Literal["lpza"],
) -> Callable[[Generator[str]], Optional[dtos.Pkmn]]:
    match parser:
        case "lpza":
            return lpza.parse_pkmn
