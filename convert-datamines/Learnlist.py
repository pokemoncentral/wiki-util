from dataclasses import dataclass, field
from typing import Literal, Self

LearnLevel = int | Literal["Inizio", "Evo"]
LearnType = Literal["LEVEL_UP", "TM", "EGG", "REMINDER"]


def parse_learnlevel(level: int) -> LearnLevel:
    if level == 0:
        return "Evo"
    if level < 2:
        return "Inizio"
    return level


@dataclass
class FormMoves:
    form_name: str
    moves_by_game: dict[str, str] = field(default_factory=dict)

    def merge_in(self, other: Self):
        self.moves_by_game = {**other.moves_by_game, **self.moves_by_game}

    def to_wikicode(self, games_order: dict[str, int]) -> str:
        form_heading = f"====={self.form_name}=====" if self.form_name else ""
        moves = sorted(self.moves_by_game.items(), key=lambda kv: games_order[kv[0]])
        return f"{form_heading}\n{'\n\n\n'.join(w for _, w in moves)}".strip()

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
    pre_evo: dict[str, FormMoves] = field(default_factory=dict)
    reminder: dict[str, FormMoves] = field(default_factory=dict)

    def merge_in(self, other: Self):
        self._merge_by_form_name(self.level_up, other.level_up)
        self._merge_by_form_name(self.tm, other.tm)
        self._merge_by_form_name(self.egg, other.egg)
        self._merge_by_form_name(self.reminder, other.reminder)
        self._merge_by_form_name(self.pre_evo, other.pre_evo)

    def to_wikicode(
        self,
        section_headings: dict[str, str],
        forms_order: dict[str, int],
        games_order: dict[str, int],
    ) -> str:
        sections = [
            f"""
===={section_headings.get("level_up", "Aumentando di [[livello]]")}====
{self._form_moves_wikicode(self.level_up, forms_order, games_order)}
            """,
            f"""
===={section_headings.get("tm", "Tramite [[MT]]")}====
{self._form_moves_wikicode(self.tm, forms_order, games_order)}
            """,
        ]

        if self.egg:
            sections.append(
                f"""
===={section_headings.get("egg", "Come [[Mossa Uovo|mosse Uovo]]")}====
{self._form_moves_wikicode(self.egg, forms_order, games_order)}
                """
            )

        if self.reminder:
            sections.append(
                f"""
===={section_headings.get("reminder", "Dall'[[Insegnamosse]]")}====
{self._form_moves_wikicode(self.reminder, forms_order, games_order)}
                """
            )

        if self.pre_evo:
            sections.append(
                f"""
===={section_headings.get("pre_evo", "Tramite [[evoluzione|evoluzioni]] precedenti")}====
{self._form_moves_wikicode(self.pre_evo, forms_order, games_order)}
                """
            )

        return "\n\n".join(map(str.strip, sections))

    @staticmethod
    def _form_moves_wikicode(
        form_moves: dict[str, FormMoves],
        form_order: dict[str, int],
        games_order: dict[str, int],
    ):
        sorted_moves = FormMoves.sorted_forms(form_moves, form_order)
        if len(sorted_moves) == 1:
            sorted_moves[0].form_name = ""
        return "\n\n".join(fm.to_wikicode(games_order) for fm in sorted_moves)

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
