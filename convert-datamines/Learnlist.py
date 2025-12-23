from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Literal, Self

LearnLevel = int | Literal["Inizio", "Evo"]
LearnType = Literal["LEVEL_UP", "TM", "EGG", "REMINDER"]


def parse_learnlevel(level: int) -> LearnLevel:
    if level == 0:
        return "Evo"
    if level < 2:
        return "Inizio"
    return level


@dataclass
class GameMoves(ABC):
    game: ClassVar[str]
    type: ClassVar[LearnType]

    def is_duplicate(self, other: Self | str) -> bool:
        return (
            isinstance(other, type(self))
            and self.game == other.game
            and self.type == other.type
        )

    @abstractmethod
    def to_render_call(self) -> str:
        ...


@dataclass
class FormMoves:
    form_name: str
    wikicode: str = ""
    moves_by_game: list[GameMoves] = field(default_factory=list)

    def merge_in(self, other: Self):
        for other_moves in other.moves_by_game:
            is_duplicate = any(
                other_moves.is_duplicate(self_game_move)
                for self_game_move in self.moves_by_game
            )
            if not is_duplicate:
                self.moves_by_game.append(other_moves)

    def to_wikicode(self, pkmn_name: str, form_abbr_by_name: dict[str, str]) -> str:
        lines = []
        if self.form_name:
            lines.append(f"===={self.form_name}====\n")
        if self.wikicode:
            lines.append(self.wikicode)

        try:
            form_param = f" form = {form_abbr_by_name[self.form_name]}"
        except KeyError:
            form_param = ""
        lines.extend(
            f"\n{game_moves.to_render_call(pkmn_name, form_param)}"
            for game_moves in self.moves_by_game
        )

        return "\n".join(lines)


@dataclass
class Learnlist:
    level_up: list[FormMoves] = field(default_factory=list)
    tm: list[FormMoves] = field(default_factory=list)
    egg: list[FormMoves] = field(default_factory=list)
    reminder: list[FormMoves] = field(default_factory=list)

    def merge_in(self, other: Self):
        self._merge_by_form_name(self.level_up, other.level_up)
        self._merge_by_form_name(self.tm, other.tm)
        self._merge_by_form_name(self.egg, other.egg)
        self._merge_by_form_name(self.reminder, other.reminder)

    @staticmethod
    def _merge_by_form_name(
        this_form_moves: list[FormMoves], other_form_moves: list[FormMoves]
    ):
        for other_moves in other_form_moves:
            try:
                this_moves = next(
                    this_moves
                    for this_moves in this_form_moves
                    if this_moves.form_name == other_moves.form_name
                )
                this_moves.merge_in(other_moves)
            except StopIteration:
                this_form_moves.append(other_moves)

    @staticmethod
    def translate_int_level(level: int) -> LearnLevel:
        if level == 0:
            return "Evo"
        if level < 2:
            return "Inizio"
        return level
