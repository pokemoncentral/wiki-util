#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
from typing import Any, Literal, Optional, Tuple

import mwparserfromhell as mwparser
import pywikibot as pwb
from dtos import Pkmn
from lpza import map_datamine
from mwparserfromhell.wikicode import Wikicode
from pywikibot.bot import CurrentPageBot

AltForms = dict[str, dict[str, str]]
DatamineLearnlistItem = Tuple[Pkmn, Tuple[str, str]]


def find_section(wikicode: Wikicode, heading: str) -> Wikicode:
    return wikicode.get_sections(matches=heading)[0]


class LpzaLearnlistSubpageBot(CurrentPageBot):
    PersistAction = Literal["u", "s", "a"]

    pkmn_page_include_regex = re.compile(r"\{\{/Mosse apprese in .+ generazione\}\}")

    alt_forms: AltForms
    current_datamine_item: DatamineLearnlistItem
    current_alt_form: dict[str, str]
    out_dir: str
    save_all: bool

    def __init__(
        self, out_dir: str, alt_forms: AltForms, *args: Any, **kwargs: dict[str, Any]
    ):
        super(LpzaLearnlistSubpageBot, self).__init__(*args, **kwargs)
        self.alt_forms = alt_forms
        self.out_dir = out_dir
        self.save_all = False

    def setup(self):
        os.makedirs(self.out_dir, exist_ok=True)

    def init_page(self, item: DatamineLearnlistItem):
        self.current_datamine_item = item
        pkmn = self.current_datamine_item[0]
        self.current_alt_form = self.alt_forms.get(pkmn.lua_table_key, dict())
        base_name = self.current_alt_form.get("baseName", pkmn.name)
        return pwb.Page(pwb.Site(), f"{base_name}/Mosse apprese in nona generazione")

    def treat_page(self):
        current_content = self._read_learnlist_page()
        new_content = (
            self._create_learnlist_subpage()
            if current_content is None
            else self._add_lpza_learnlists(current_content)
        )

        action = self._ask_action(new_content)
        self._persist_page(action, new_content)

    @property
    def _current_form_heading(self) -> str:
        try:
            return f"====={self.current_alt_form['formName']}=====\n"
        except KeyError:
            return ""

    @property
    def _current_out_file(self) -> str:
        file_name = self.current_page.title().replace("/", "--") + ".txt"
        return os.path.join(self.out_dir, file_name)

    def _add_lpza_learnlists(self, current_learnlist: str) -> str:
        _, (lpza_level, lpza_tm) = self.current_datamine_item

        wikicode = mwparser.parse(current_learnlist)

        if lpza_level not in current_learnlist:
            level_up_section = find_section(wikicode, r"Aumentando di \[\[livello\]\]")
            level_up_section.append(f"{self._current_form_heading}{lpza_level}\n\n")

        if lpza_tm not in current_learnlist:
            tm_section = find_section(wikicode, r"Tramite \[\[MT\]\]")
            tm_section.append(f"{self._current_form_heading}{lpza_tm}\n\n")

        return str(wikicode)

    def _ask_action(self, new_content: str) -> PersistAction:
        if self.save_all:
            return "s"
        if self.opt["always"]:
            return "u"

        pwb.output(
            f"Differences to {self.current_page.title()} after adding LPZA learnlist:"
        )
        pwb.showDiff(self.current_page.text, new_content)
        answer = pwb.input_choice(
            "What to do?",
            (
                ("upload page", "u"),
                ("save locally", "s"),
                ("save all", "a"),
            ),
        )

        self.save_all = self.save_all or answer == "a"
        return answer

    def _create_learnlist_subpage(self) -> str:
        pkmn, (lpza_level, lpza_tm) = self.current_datamine_item
        return f"""
====Aumentando di [[livello]]====
{self._current_form_heading}{lpza_level}

====Tramite [[MT]]====
{self._current_form_heading}{lpza_tm}

<noinclude>
[[Categoria:Sottopagine moveset Pokémon (nona generazione)]]
[[en:{pkmn.name} (Pokémon)/Generation IX learnset]]
</noinclude>
""".strip()

    def _persist_page(self, action: PersistAction, new_content: str):
        match action:
            case "u":
                if not self.current_page.exists():
                    self._use_new_learnlist_in_pkmn_page()
                self.put_current(
                    new_content,
                    summary="Add LPZA learnlists",
                    show_diff=False,
                    force=True,
                )

            case "a" | "s":
                pwb.output(f"Saving to {self._current_out_file}")
                with open(self._current_out_file, "w", encoding="utf-8") as f:
                    f.write(new_content)

            case _:
                raise ValueError(f"Unknown action: {action}")

    def _read_learnlist_page(self) -> Optional[str]:
        try:
            with open(self._current_out_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return self.current_page.text if self.current_page.exists() else None

    def _use_new_learnlist_in_pkmn_page(self):
        pkmn = self.current_datamine_item[0]
        pwb.output(f"Updating {pkmn.name} to use ninth generation learnlists")
        pkmn_page = pwb.Page(pwb.Site(), pkmn.name)
        new_text = self.pkmn_page_include_regex.sub(
            "{{/Mosse apprese in nona generazione}}", pkmn_page.text
        )
        self.userPut(
            pkmn_page,
            pkmn_page.text,
            new_text,
            summary="Use ninth generation learnlists",
        )


def main(args: list[str]):
    [datamine_file, alt_forms_file, out_dir] = pwb.handle_args(args)
    with open(alt_forms_file, encoding="utf-8") as f:
        alt_forms = json.load(f)
    LpzaLearnlistSubpageBot(
        out_dir, alt_forms, generator=map_datamine("learnlist", datamine_file)
    ).run()


if __name__ == "__main__":
    main(sys.argv[1:])
