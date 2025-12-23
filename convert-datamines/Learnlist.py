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

    @abstractmethod
    def to_render_call(self) -> str:
        ...


@dataclass
class FormMoves:
    form_name: str
    wikicode: str = ""
    moves_by_game: dict[str, GameMoves] = field(default_factory=dict)

    def merge_in(self, other: Self):
        self.moves_by_game = {**other.moves_by_game, **self.moves_by_game}

    def to_wikicode(
        self,
        pkmn_name: str,
        form_abbr_by_name: dict[str, str],
        games_order: dict[str, int],
    ) -> str:
        lines = []
        if self.form_name:
            lines.append(f"===={self.form_name}====\n")
        if self.wikicode:
            lines.append(self.wikicode)

        try:
            form_param = f" form = {form_abbr_by_name[self.form_name]}"
        except KeyError:
            form_param = ""
        sorted_games = sorted(
            self.moves_by_game.items(), key=lambda kv: games_order[kv[0]]
        )
        lines.extend(
            f"\n{game_moves.to_render_call(pkmn_name, form_param)}"
            for _, game_moves in sorted_games
        )

        return "\n".join(lines)

    @staticmethod
    def sorted_forms(
        form_moves: dict[str, Self], forms_order: dict[str, int]
    ) -> list[Self]:
        return sorted(
            form_moves.values(), key=lambda f: forms_order.get(f.form_name, -1)
        )


@dataclass
class Learnlist:
    level_up: dict[str, FormMoves] = field(default_factory=dict)
    tm: dict[str, FormMoves] = field(default_factory=dict)
    egg: dict[str, FormMoves] = field(default_factory=dict)
    reminder: dict[str, FormMoves] = field(default_factory=dict)

    def merge_in(self, other: Self):
        self._merge_by_form_name(self.level_up, other.level_up)
        self._merge_by_form_name(self.tm, other.tm)
        self._merge_by_form_name(self.egg, other.egg)
        self._merge_by_form_name(self.reminder, other.reminder)

    @staticmethod
    def _merge_by_form_name(
        this_form_moves: dict[str, FormMoves], other_form_moves: dict[str, FormMoves]
    ):
        for form_name, other_moves in other_form_moves.items():
            try:
                this_moves = this_form_moves[form_name]
                this_moves.merge_in(other_moves)
            except KeyError:
                this_form_moves[form_name] = other_moves
