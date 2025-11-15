#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from parser.lpza import parse
from typing import Any, Optional, Tuple

import mwparserfromhell as mwparser
import pywikibot as pwb
from altforms import AltForms, SingleAltForm
from dtos import Pkmn
from LearnlistSubpageBot import LearnlistSubpageBot


class LpzaLearnlistBot(LearnlistSubpageBot):
    def __init__(self, *args: Any, **kwargs: dict[str, Any]):
        super(LpzaLearnlistBot, self).__init__(
            *args,
            it_gen_ord="nona",
            roman_gen="IX",
            summary="Add LPZA learnlists",
            **kwargs,
        )

    def create_learnlist_subpage(self, pkmn: Pkmn, form_data: Optional[AltForms]):
        return f"""
====Aumentando di [[livello]]====
{self._serialize_level_up(pkmn, form_data)}

====Tramite [[MT]]====
{self._serialize_tm(pkmn, form_data)}

<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({self.it_gen_ord} generazione)]]
[[en:{pkmn.name} (Pokémon)/Generation {self.roman_gen} learnset]]
</noinclude>
""".strip()

    def add_learnlist(
        self, current_learnlist: str, pkmn: Pkmn, form_data: Optional[SingleAltForm]
    ):
        wikicode = mwparser.parse(current_learnlist)

        new_level_up = self._serialize_level_up(pkmn, form_data)
        if new_level_up not in current_learnlist:
            level_up_section = self.find_section(
                wikicode, r"Aumentando di \[\[livello\]\]"
            )
            level_up_section.append(f"{new_level_up}\n\n")

        new_tm = self._serialize_tm(pkmn, form_data)
        if new_tm not in current_learnlist:
            tm_section = self.find_section(wikicode, r"Tramite \[\[MT\]\]")
            tm_section.append(f"{new_tm}\n\n")

        return str(wikicode)

    @classmethod
    def _serialize_level_up(cls, pkmn: Pkmn, form_data: Optional[SingleAltForm]) -> str:
        form_heading, form_param = cls._make_form_texts(form_data)
        return f"""
{form_heading}{{{{#invoke: Learnlist-LPZA | level | {pkmn.name} |{form_param} //
{"\n".join(        f"| {level} | {plus_level} | {name} | //"
        for level, plus_level, name in pkmn.moves.level_up
)}
}}}}
""".strip()

    @classmethod
    def _serialize_tm(cls, pkmn: Pkmn, form_data: Optional[SingleAltForm]) -> str:
        form_heading, form_param = cls._make_form_texts(form_data)
        return f"""
{form_heading}{{{{#invoke: Learnlist-LPZA | tm | {pkmn.name} |{form_param} //
{"\n".join(f"| {tm} | {name} | //" for tm, name in pkmn.moves.tm)}
}}}}
""".strip()

    @staticmethod
    def _make_form_texts(form_data: Optional[SingleAltForm]) -> Tuple[str, str]:
        if form_data is None:
            return ("", "")

        form_heading = f"====={form_data.name}=====\n"
        form_param = f" form = {form_data.abbr} |" if form_data.abbr != "base" else ""
        return (form_heading, form_param)


def main(args: list[str]):
    [datamine_file, alt_forms_file, out_dir] = pwb.handle_args(args)

    alt_forms = AltForms.from_json(alt_forms_file)
    generator = parse(datamine_file)

    LpzaLearnlistBot(alt_forms, out_dir, generator).run()


if __name__ == "__main__":
    main(sys.argv[1:])
