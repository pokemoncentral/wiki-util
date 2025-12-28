# -*- coding: utf-8 -*-

import os
import re
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional

import jsonpickle
import pywikibot as pwb
from altforms import AltForms
from dtos import Pkmn
from Learnlist import Learnlist
from pywikibot.bot import CurrentPageBot


class LearnlistSubpageBot(CurrentPageBot, ABC):
    pkmn_page_include_regex = re.compile(r"\{\{/Mosse apprese in .+ generazione\}\}")

    alt_forms: dict[str, AltForms]
    it_gen_ord: str
    roman_gen: str
    summary: str
    cache_dir: str
    out_dir: Optional[str]

    pkmn: Pkmn
    alt_form: Optional[AltForms]

    def __init__(
        self,
        alt_forms: AltForms,
        generator: Generator[Pkmn],
        *args: Any,
        it_gen_ord: str,
        roman_gen: str,
        summary: str,
        cache_dir: Optional[str] = None,
        out_dir: Optional[str] = None,
        **kwargs: dict[str, Any],
    ):
        super(LearnlistSubpageBot, self).__init__(*args, generator=generator, **kwargs)
        self.alt_forms = alt_forms
        self.it_gen_ord = it_gen_ord
        self.roman_gen = roman_gen
        self.summary = summary
        self.cache_dir = cache_dir or f"learnlist-subpages/{roman_gen}/cache"
        self.out_dir = out_dir

    @abstractmethod
    def make_learnlist_from_datamine(self, pkmn: Pkmn, form_name: str) -> Learnlist:
        ...

    @abstractmethod
    def parse_learnlist_subpage(
        self, learnlist_subpage: str, pkmn_name: str
    ) -> Learnlist:
        ...

    @abstractmethod
    def serialize_learnlist_subpage(
        self,
        learnlist: Learnlist,
        pkmn_name: str,
        form_order_by_name: dict[str, int],
    ) -> str:
        ...

    def setup(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        if self.out_dir is not None:
            os.makedirs(self.out_dir, exist_ok=True)

    def init_page(self, item: Pkmn):
        self.pkmn = item

        alt_form = self.alt_forms.get(self.pkmn.name.lower())
        self.alt_form = (
            alt_form.for_abbr(self.pkmn.form_abbr or "base")
            if alt_form is not None
            else None
        )

        base_name = (
            self.alt_form.base_name if self.alt_form is not None else self.pkmn.name
        )
        subpage_name = f"Mosse apprese in {self.it_gen_ord} generazione"
        return pwb.Page(pwb.Site(), f"{base_name}/{subpage_name}")

    def treat_page(self):
        # Mega evolutions have the same learnlist as the base form
        if self.alt_form is not None and self.alt_form.is_mega:
            return

        file_name = self.current_page.title().replace("/", "--") + ".json"
        cache_file = os.path.join(self.cache_dir, file_name)

        try:
            pwb.output(f"Read from {cache_file}")
            with open(cache_file, "r", encoding="utf-8") as f:
                learnlist = jsonpickle.loads(f.read())
        except FileNotFoundError:
            learnlist = (
                self.parse_learnlist_subpage(self.current_page.text, self.pkmn.name)
                if self.current_page.exists()
                else Learnlist()
            )

        datamine_learnlist = self.make_learnlist_from_datamine(
            self.pkmn,
            self.alt_form.name if self.alt_form is not None else self.pkmn.name,
        )
        learnlist.merge_in(datamine_learnlist)

        pwb.output(f"Saving to {cache_file}")
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(jsonpickle.dumps(learnlist))

    def teardown(self):
        for cache_file in os.listdir(self.cache_dir):
            cache_file_path = os.path.join(self.cache_dir, cache_file)
            with open(cache_file_path, "r", encoding="utf-8") as f:
                learnlist = jsonpickle.loads(f.read())

            subpage_title = os.path.splitext(cache_file)[0].replace("--", "/")
            pkmn_name = os.path.dirname(subpage_title)
            try:
                alt_form = next(
                    alt_form
                    for alt_form in self.alt_forms.values()
                    if alt_form.base_name == pkmn_name
                )
                forms_order_by_name = {
                    name: alt_form.gamesOrder.index(abbr)
                    for abbr, name in alt_form.names.items()
                }
            except StopIteration:
                forms_order_by_name = {}

            subpage_content = self.serialize_learnlist_subpage(
                learnlist, pkmn_name, forms_order_by_name
            )

            if self.out_dir:
                out_file = os.path.join(
                    self.out_dir, f"{os.path.splitext(cache_file)[0]}.wikicode"
                )
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(subpage_content)

            page = pwb.Page(pwb.Site(), subpage_title)

            # if not page.exists():
            #     self._use_new_learnlist_in_pkmn_page()
            # self.userPut(
            #     page, page.text, subpage_content, summary=self.summary, show_diff=True
            # )

    def _use_new_learnlist_in_pkmn_page(self):
        pkmn = self.pkmn[0]
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
