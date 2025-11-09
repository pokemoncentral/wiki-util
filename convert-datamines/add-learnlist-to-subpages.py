#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import Tuple

import mwparserfromhell as mwparser
import pywikibot as pwb
from dtos import Pkmn
from lpza import map_datamine
from mwparserfromhell.wikicode import Wikicode
from pywikibot.bot import CurrentPageBot

DatamineLearnlistItem = Tuple[Pkmn, Tuple[str, str]]


def find_section(wikicode: Wikicode, heading: str) -> Wikicode:
    return wikicode.get_sections(matches=heading)[0]


class LpzaLearnlistSubpageBot(CurrentPageBot):
    out_dir: str
    current_datamine_item: DatamineLearnlistItem
    save_all: bool

    def __init__(self, out_dir, *args, **kwargs):
        super(LpzaLearnlistSubpageBot, self).__init__(*args, **kwargs)
        self.out_dir = out_dir
        self.save_all = False

    def setup(self):
        os.makedirs(self.out_dir, exist_ok=True)

    def init_page(self, item: DatamineLearnlistItem):
        self.current_datamine_item = item
        return pwb.Page(pwb.Site(), f"{item[0].name}/Mosse apprese in nona generazione")

    def treat_page(self):
        new_content = (
            self._add_lpza_learnlists()
            if self.current_page.exists()
            else self._create_learnlist_subpage()
        )
        self._persist_page(new_content)

    def _add_lpza_learnlists(self) -> str:
        _, (lpza_level, lpza_tm) = self.current_datamine_item
        wikicode = mwparser.parse(self.current_page.text)

        level_up_section = find_section(wikicode, r"Aumentando di \[\[livello\]\]")
        level_up_section.append(f"{lpza_level}\n\n")

        tm_section = find_section(wikicode, r"Tramite \[\[MT\]\]")
        tm_section.append(f"{lpza_tm}\n\n")

        return str(wikicode)

    def _create_learnlist_subpage(self) -> str:
        pkmn, (lpza_level, lpza_tm) = self.current_datamine_item
        return f"""
====Aumentando di [[livello]]====
{lpza_level}

====Tramite [[MT]]====
{lpza_tm}

<noinclude>
[[Categoria:Sottopagine moveset Pokémon (nona generazione)]]
[[en:{pkmn.name} (Pokémon)/Generation IX learnset]]
</noinclude>
""".strip()

    def _persist_page(self, new_content: str):
        if self.save_all:
            answer = "s"
        else:
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
        match answer:
            case "u":
                self.put_current(new_content, show_diff=False, force=True)

            case "a" | "s":
                file_name = self.current_page.title().replace("/", "--") + ".txt"
                pwb.output(f"Saving to {file_name}")
                with open(os.path.join(self.out_dir, file_name), "w") as f:
                    f.write(new_content)

            case _:
                raise ValueError(f"Unknown answer: {answer}")


def main(args: list[str]):
    [datamine_file, out_dir] = pwb.handle_args(args)
    LpzaLearnlistSubpageBot(
        out_dir, generator=map_datamine("learnlist", datamine_file)
    ).run()


if __name__ == "__main__":
    main(sys.argv[1:])
