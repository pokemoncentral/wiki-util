#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
from parser.lpza import parse
from typing import Any, Optional

import pywikibot as pwb
from altforms import AltForms
from dtos import Pkmn
from Learnlist import FormMoves, Learnlist
from LearnlistSubpageBot import LearnlistSubpageBot


class LpzaLearnlistBot(LearnlistSubpageBot):
    def __init__(
        self,
        cache_dir: str,
        out_dir: Optional[str],
        *args: Any,
        **kwargs: dict[str, Any],
    ):
        super(LpzaLearnlistBot, self).__init__(
            *args,
            it_gen_ord="nona",
            roman_gen="IX",
            summary="Add LPZA learnlists",
            cache_dir=cache_dir,
            out_dir=out_dir,
            **kwargs,
        )

    def make_learnlist_from_datamine(self, pkmn: Pkmn, form_name: str) -> Learnlist:
        form_param = "" if pkmn.form_abbr is None else f" form = {pkmn.form_abbr}"
        return Learnlist(
            level_up={
                form_name: FormMoves(
                    form_name,
                    {"LPZA": self._level_up_wikicode(pkmn, form_param)},
                )
            },
            tm={
                form_name: FormMoves(
                    form_name, {"LPZA": self._tm_wikicode(pkmn, form_param)}
                )
            },
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
            is_prop_heading = not is_form_heading and line.startswith("====")

            if current_render and (is_end or is_form_heading or is_prop_heading):
                current_moves = getattr(learnlist, current_prop)
                if form_name not in current_moves:
                    current_moves[form_name] = FormMoves(form_name, {"SV": ""})
                current_moves[form_name].moves_by_game["SV"] = "\n".join(current_render)
                current_render.clear()

            if is_prop_heading:
                if "livello" in line:
                    current_prop = "level_up"
                elif "MT" in line:
                    current_prop = "tm"
                elif "Uovo" in line:
                    current_prop = "egg"
                elif "precedenti" in line:
                    current_prop = "pre_evo"
                elif "Insegnamosse" in line:
                    current_prop = "reminder"
                else:
                    raise ValueError(f"Unknown heading: {line}")
                setattr(learnlist, current_prop, {})

            if is_form_heading:
                form_name = line.strip("=")

            if is_end:
                break

            if is_prop_heading or is_form_heading:
                continue

            current_render.append(line)

        return learnlist

    def serialize_learnlist_subpage(
        self,
        learnlist: Learnlist,
        pkmn_name: str,
        form_order_by_name: dict[str, int],
    ) -> str:
        sections = [
            f"""
====Aumentando di [[livello]]====
{self._form_moves_list_to_wikicode(learnlist.level_up, form_order_by_name)}
            """,
            f"""
====Tramite [[MT]]====
{self._form_moves_list_to_wikicode(learnlist.tm, form_order_by_name)}
            """,
            f"""
====Come [[Mossa Uovo#Pokémon Scarlatto e Violetto|mosse Uovo]]====
{self._form_moves_list_to_wikicode(learnlist.egg, form_order_by_name)}
            """,
        ]

        if learnlist.reminder:
            sections.append(
                f"""
====Dall'[[Insegnamosse]]====
{self._form_moves_list_to_wikicode(learnlist.reminder, form_order_by_name)}
                """
            )

        if learnlist.pre_evo:
            sections.append(
                f"""
====Tramite [[evoluzione|evoluzioni]] precedenti====
{self._form_moves_list_to_wikicode(learnlist.pre_evo, form_order_by_name)}
                """
            )

        sections.append(
            f"""
<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({self.it_gen_ord} generazione)]]
[[en:{pkmn_name} (Pokémon)/Generation {self.roman_gen} learnset]]
</noinclude>
            """
        )

        return "\n\n".join(map(str.strip, sections))

    @staticmethod
    def _form_moves_list_to_wikicode(
        form_moves: list[FormMoves],
        form_order_by_name: dict[str, int],
    ) -> str:
        return "\n\n".join(
            fm.to_wikicode({"SV": 0, "LPZA": 1})
            for fm in FormMoves.sorted_forms(form_moves, form_order_by_name)
        )

    @staticmethod
    def _level_up_wikicode(pkmn: Pkmn, form_param: str) -> str:
        entries = (
            f"| {level} | {plus_level} | {name} | //"
            for level, plus_level, name in pkmn.moves.level_up
        )
        return f"""
{{{{#invoke: Learnlist/LPZA | level | {pkmn.name} |{form_param} //
{"\n".join(entries)}
}}}}
""".strip()

    @staticmethod
    def _tm_wikicode(pkmn: Pkmn, form_param: str) -> str:
        return f"""
{{{{#invoke: Learnlist/LPZA | tm | {pkmn.name} |{form_param} //
{"\n".join(f"| {tm} | {name} | {"yes | " if name in pkmn.moves.alpha else ""}//" for tm, name in pkmn.moves.tm)}
}}}}
""".strip()


def main(args: list[str]):
    [datamine_file, alt_forms_file, cache_dir, *rest] = pwb.handle_args(args)
    try:
        out_dir = rest[0]
    except IndexError:
        out_dir = None

    alt_forms = AltForms.from_json(alt_forms_file)
    generator = parse(datamine_file)

    LpzaLearnlistBot(cache_dir, out_dir, alt_forms, generator).run()


if __name__ == "__main__":
    main(sys.argv[1:])
