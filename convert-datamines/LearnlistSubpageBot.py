# -*- coding: utf-8 -*-

import os
import re
from abc import ABC, abstractmethod
from typing import Any, Generator, Literal, Optional

import pywikibot as pwb
from altforms import AltForms, SingleAltForm
from dtos import Pkmn
from mwparserfromhell.wikicode import Wikicode
from pywikibot.bot import CurrentPageBot


class LearnlistSubpageBot(CurrentPageBot, ABC):
    PersistAction = Literal["u", "s", "a"]

    pkmn_page_include_regex = re.compile(r"\{\{/Mosse apprese in .+ generazione\}\}")

    alt_forms: dict[str, AltForms]
    it_gen_ord: str
    out_dir: str
    roman_gen: str
    summary: str

    current_pkmn: Pkmn
    current_alt_form: Optional[AltForms]
    save_all: bool

    def __init__(
        self,
        alt_forms: AltForms,
        out_dir: str,
        generator: Generator[Pkmn],
        *args: Any,
        it_gen_ord: str,
        roman_gen: str,
        summary: str,
        **kwargs: dict[str, Any],
    ):
        super(LearnlistSubpageBot, self).__init__(*args, generator=generator, **kwargs)
        self.alt_forms = alt_forms
        self.it_gen_ord = it_gen_ord
        self.out_dir = out_dir
        self.roman_gen = roman_gen
        self.summary = summary

        self.save_all = False

    @abstractmethod
    def add_learnlist(
        self, current_learnlist: str, pkmn: Pkmn, form_data: Optional[SingleAltForm]
    ) -> str:
        ...

    @abstractmethod
    def create_learnlist_subpage(
        self, pkmn: Pkmn, form_data: Optional[SingleAltForm]
    ) -> str:
        ...

    def setup(self):
        os.makedirs(self.out_dir, exist_ok=True)

    def init_page(self, item: Pkmn):
        self.current_pkmn = item
        self.current_alt_form = self.alt_forms.get(self.current_pkmn.name.lower())
        base_name = (
            self.current_alt_form.base_name
            if self.current_alt_form is not None
            else self.current_pkmn.name
        )
        subpage_name = f"Mosse apprese in {self.it_gen_ord} generazione"
        return pwb.Page(pwb.Site(), f"{base_name}/{subpage_name}")

    def treat_page(self):
        single_alt_form = (
            self.current_alt_form.for_abbr(self.current_pkmn.form_abbr or "base")
            if self.current_alt_form is not None
            else None
        )

        # Mega evolutions have the same learnlist as the base form
        if single_alt_form is not None and single_alt_form.name.startswith("Mega"):
            return

        current_content = self._read_learnlist_page()
        new_content = (
            self.create_learnlist_subpage(self.current_pkmn, single_alt_form)
            if current_content is None
            else self.add_learnlist(current_content, self.current_pkmn, single_alt_form)
        )

        action = self._ask_action(new_content)
        self._persist_page(action, new_content)

    @staticmethod
    def find_section(wikicode: Wikicode, heading: str) -> Wikicode:
        return wikicode.get_sections(matches=heading)[0]

    @property
    def _current_out_file(self) -> str:
        file_name = self.current_page.title().replace("/", "--") + ".txt"
        return os.path.join(self.out_dir, file_name)

    def _ask_action(self, new_content: str) -> PersistAction:
        if self.save_all:
            return "s"
        if self.opt["always"]:
            return "u"

        pwb.output(
            f"Differences to {self.current_page.title()} after adding learnlists:"
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

    def _persist_page(self, action: PersistAction, new_content: str):
        match action:
            case "u":
                if not self.current_page.exists():
                    self._use_new_learnlist_in_pkmn_page()
                self.put_current(
                    new_content,
                    summary=self.summary,
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
        pkmn = self.current_pkmn[0]
        pwb.output(
            f"Updating {pkmn.name} to use {self.roman_gen} generation learnlists"
        )
        pkmn_page = pwb.Page(pwb.Site(), pkmn.name)
        new_text = self.pkmn_page_include_regex.sub(
            f"{{{{/Mosse apprese in {self.it_gen_ord} generazione}}}}", pkmn_page.text
        )
        self.userPut(
            pkmn_page,
            pkmn_page.text,
            new_text,
            summary=f"Use {self.roman_gen} generation learnlists",
        )
