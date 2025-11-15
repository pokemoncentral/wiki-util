#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from parser.lpza import parse
from typing import Optional

import mwparserfromhell as mwparser
import pywikibot as pwb
from altforms import AltForms, SingleAltForm
from dtos import Pkmn
from LearnlistSubpageBot import LearnlistSubpageBot


class LpzaLearnlistBot(LearnlistSubpageBot):
    def create_learnlist_subpage(self, pkmn: Pkmn, form_data: Optional[AltForms]):
        form_heading = self._make_form_heading(form_data)
        return f"""
====Aumentando di [[livello]]====
{self._serialize_level_up(pkmn, form_heading)}

====Tramite [[MT]]====
{self._serialize_tm(pkmn, form_heading)}

<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({self.it_gen_ord} generazione)]]
[[en:{pkmn.name} (Pokémon)/Generation {self.roman_gen} learnset]]
</noinclude>
""".strip()

    def add_learnlist(
        self, current_learnlist: str, pkmn: Pkmn, form_data: Optional[SingleAltForm]
    ):
        # Mega evolutions have the same learnlist as the base form
        if form_data is not None and form_data.name.startswith("Mega"):
            return current_learnlist

        wikicode = mwparser.parse(current_learnlist)
        form_heading = self._make_form_heading(form_data)

        level_up_section = self.find_section(wikicode, r"Aumentando di \[\[livello\]\]")
        level_up_section.append(f"{self._serialize_level_up(pkmn, form_heading)}\n\n")

        tm_section = self.find_section(wikicode, r"Tramite \[\[MT\]\]")
        tm_section.append(f"{self._serialize_tm(pkmn, form_heading)}\n\n")

        return str(wikicode)

    @staticmethod
    def _make_form_heading(form_data: Optional[SingleAltForm]) -> str:
        return f"====={form_data.name}=====\n" if form_data is not None else ""

    @staticmethod
    def _serialize_level_up(pkmn: Pkmn, form_heading: str) -> str:
        return f"""
{form_heading}{{{{#invoke: Learnlist-LPZA | level | {pkmn.name} | //
{"\n".join(        f"| {level} | {plus_level} | {name} | //"
        for level, plus_level, name in pkmn.moves.level_up
)}
}}}}
""".strip()

    @staticmethod
    def _serialize_tm(pkmn: Pkmn, form_heading: str) -> str:
        return f"""
{form_heading}{{{{#invoke: Learnlist-LPZA | tm | {pkmn.name} | //
{"\n".join(f"| {tm} | {name} | //" for tm, name in pkmn.moves.tm)}
}}}}
""".strip()


def main(args: list[str]):
    [datamine_file, alt_forms_file, out_dir] = pwb.handle_args(args)

    alt_forms = AltForms.from_json(alt_forms_file)
    generator = parse(datamine_file)

    LpzaLearnlistBot(
        alt_forms=alt_forms,
        it_gen_ord="nona",
        out_dir=out_dir,
        roman_gen="IX",
        summary="Add LPZA learnlists",
        generator=generator,
    ).run()


if __name__ == "__main__":
    main(sys.argv[1:])
