# -*- coding: utf-8 -*-

import os
import re
from abc import ABC, abstractmethod
from typing import Any, Generator, Optional

import jsonpickle
import pywikibot as pwb
from altforms import AltForms
from dtos import Moves, Pkmn
from Learnlist import Learnlist
from pywikibot.bot import CurrentPageBot


class LearnlistSubpageBot(CurrentPageBot, ABC):
    pkmn_page_include_regex = re.compile(r"\{\{/Mosse apprese in .+ generazione\}\}")

    alt_forms: dict[str, AltForms]
    it_gen_ord: str
    cache_dir: str
    roman_gen: str
    summary: str

    current_pkmn: Pkmn
    current_alt_form: Optional[AltForms]

    def __init__(
        self,
        alt_forms: AltForms,
        cache_dir: str,
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
        self.cache_dir = cache_dir
        self.roman_gen = roman_gen
        self.summary = summary

    @abstractmethod
    def make_learnlist_from_datamine(self, pkmn: Pkmn, form_name: str) -> Learnlist:
        ...

    @abstractmethod
    def parse_learnlist_subpage(self, learnlist_subpage: str) -> Learnlist:
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
        form_abbr = self.current_pkmn.form_abbr or "base"
        single_alt_form = (
            self.current_alt_form.for_abbr(form_abbr)
            if self.current_alt_form is not None
            else None
        )

        form_name = single_alt_form.name if single_alt_form is not None else None
        # Mega evolutions have the same learnlist as the base form
        if form_name is not None and form_name.startswith("Mega"):  # Meganium???
            return

        new_learnlist = self.make_learnlist_from_datamine(
            self.current_pkmn, form_name if form_abbr != "base" else ""
        )
        learnlist = self._read_current_learnlist()
        if learnlist is not None:
            learnlist.merge_in(new_learnlist)
        else:
            learnlist = new_learnlist
        self._save_learnlist_cache(learnlist)

    def teardown(self):
        for cache_file in os.listdir(self.cache_dir):
            with open(os.path.join(self.cache_dir, cache_file), "r") as f:
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
            print(subpage_content)

            page = pwb.Page(pwb.Site(), subpage_title)

            # if not page.exists():
            #     self._use_new_learnlist_in_pkmn_page()
            # self.userPut(
            #     page, page.text, subpage_content, summary=self.summary, show_diff=True
            # )

    @property
    def _current_cache_file(self) -> str:
        file_name = self.current_page.title().replace("/", "--") + ".json"
        return os.path.join(self.cache_dir, file_name)

    def _read_current_learnlist(self) -> Optional[Learnlist]:
        try:
            pwb.output(f"Read from {self._current_cache_file}")
            with open(self._current_cache_file, "r", encoding="utf-8") as f:
                learnlist = jsonpickle.loads(f.read())

            if not isinstance(learnlist, Learnlist):
                raise TypeError(f"Bad JSON in {self._current_cache_file}")
            return learnlist

        except FileNotFoundError:
            if not self.current_page.exists():
                return None
            return self.parse_learnlist_subpage(self.current_page.text)

    def _save_learnlist_cache(self, learnlist: Learnlist):
        pwb.output(f"Saving to {self._current_cache_file}")
        with open(self._current_cache_file, "w", encoding="utf-8") as f:
            f.write(jsonpickle.dumps(learnlist))

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
