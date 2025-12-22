#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from dataclasses import dataclass
from parser.lpza import LpzaLevelUpMove, parse
from typing import Any, Tuple

import pywikibot as pwb
from altforms import AltForms
from dtos import Moves
from Learnlist import FormMoves, GameMoves, Learnlist
from LearnlistSubpageBot import LearnlistSubpageBot


@dataclass
class LpzaLevelUpMoves(GameMoves):
    game = "LPZA"
    type = "LEVEL_UP"
    moves: list[LpzaLevelUpMove]

    def to_render_call(self, pkmn_name: str, form_param: str) -> str:
        return f"""
{{{{#invoke: Learnlist-LPZA | level | {pkmn_name} |{form_param} //
{"\n".join(f"| {level} | {plus_level} | {name} | //" for level, plus_level, name in self.moves)}
}}}}
""".strip()


@dataclass
class LpzaTmMoves(GameMoves):
    game = "LPZA"
    type = "TM"
    moves: list[Tuple[str, str]]

    def to_render_call(self, pkmn_name: str, form_param: str) -> str:
        return f"""
{{{{#invoke: Learnlist-LPZA | tm | {pkmn_name} |{form_param} //
{"\n".join(f"| {tm} | {name} | //" for tm, name in self.moves)}
}}}}
""".strip()


class LpzaLearnlistBot(LearnlistSubpageBot):
    def __init__(self, *args: Any, **kwargs: dict[str, Any]):
        super(LpzaLearnlistBot, self).__init__(
            *args,
            it_gen_ord="nona",
            roman_gen="IX",
            summary="Add LPZA learnlists",
            **kwargs,
        )

    def make_learnlist(self, moves: Moves, form_name: str) -> Learnlist:
        return Learnlist(
            [FormMoves(form_name, [LpzaLevelUpMoves(moves.level_up)])],
            [FormMoves(form_name, [LpzaTmMoves(moves.tm)])],
            [FormMoves(form_name, [])],
            [FormMoves(form_name, [])],
        )

    def parse_learnlist_subpage(self, learnlist_subpage: str) -> Learnlist:
        learnlist = Learnlist()
        current_prop = None
        form_name = ""
        current_render = []
        non_empty_lines = filter(
            None, map(str.strip, learnlist_subpage.split(os.linesep))
        )
        for line in non_empty_lines:
            is_end = "noinclude" in line
            is_form_heading = line.startswith("=====")
            is_prop_heading = line.startswith("====")

            if current_render and (is_end or is_form_heading or is_prop_heading):
                current_moves = getattr(learnlist, current_prop)
                if not current_moves:
                    current_moves.append(FormMoves(form_name, []))
                current_moves[-1].moves_by_game.append("\n".join(current_render))
                current_render.clear()

            if is_prop_heading:
                if "livello" in line:
                    current_prop = "level_up"
                if "MT" in line:
                    current_prop = "tm"
                if "Uovo" in line:
                    current_prop = "egg"
                setattr(learnlist, current_prop, [])

            if is_form_heading:
                form_name = line.strip("=")

            if is_end:
                break

            if is_prop_heading or is_form_heading:
                continue

            current_render.append(line)

        return learnlist

    def serialize_learnlist_subpage(
        self, learnlist: Learnlist, pkmn_name: str, form_abbr_by_name: dict[str, str]
    ) -> str:
        return f"""
====Aumentando di [[livello]]====
{"\n\n".join(form_moves.to_wikicode(pkmn_name, form_abbr_by_name) for form_moves in learnlist.level_up)}

====Tramite [[MT]]====
{"\n\n".join(form_moves.to_wikicode(pkmn_name, form_abbr_by_name) for form_moves in learnlist.tm)}

====Come [[Mossa Uovo#Pokémon Scarlatto e Violetto|mosse Uovo]]====
{"\n\n".join(form_moves.to_wikicode(pkmn_name, form_abbr_by_name) for form_moves in learnlist.egg)}

<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({self.it_gen_ord} generazione)]]
[[en:{pkmn_name} (Pokémon)/Generation {self.roman_gen} learnset]]
</noinclude>
""".strip()


def main(args: list[str]):
    [datamine_file, alt_forms_file, out_dir] = pwb.handle_args(args)

    alt_forms = AltForms.from_json(alt_forms_file)
    generator = parse(datamine_file)

    LpzaLearnlistBot(alt_forms, out_dir, generator).run()


if __name__ == "__main__":
    main(sys.argv[1:])
