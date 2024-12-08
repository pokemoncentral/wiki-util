#!/usr/bin/python
# -*- coding: utf-8 -*-

import itertools
import re
import shlex
from collections import defaultdict

import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot.bot import ExistingPageBot, SingleSiteBot


class AffectedPages:
    def __init__(self):
        self.episodes = []
        self.files = {}
        self.backlinks = defaultdict(list)

    def add_episode(self, episode):
        self.episodes.append(episode)

        for backlink in episode.backlinks():
            self.backlinks[backlink].append(episode)

        for file in episode.imagelinks():
            file_name = file.title()
            is_episode_file = any(title in file_name for title in self._episode_titles)
            if not is_episode_file:
                continue

            self.files[file] = episode
            for usage in file.using_pages():
                if usage not in self.episodes:
                    self.backlinks[usage].append(file)

    items_separator = "\n    "

    def pretty_print(self):
        backlinks = self.items_separator.join(
            f"{backlink.title()} ({', '.join(self._titles(episodes))})"
            for backlink, episodes in self.backlinks.items()
        )
        files = self.items_separator.join(
            f"{file.title()} ({episode.title()})"
            for file, episode in self.files.items()
        )
        return f"""
Episodes:
    {self.items_separator.join(self._episode_titles)}

Backlinks:
    {backlinks}

Files:
    {files}
""".strip()

    @property
    def _episode_titles(self):
        return (e.title() for e in self.episodes)

    @staticmethod
    def _titles(pages):
        return (p.title() for p in pages)


class MoveBrutalBot(SingleSiteBot, ExistingPageBot):
    def __init__(self, from_to_pairs, extras, page_list_output, *args, **kwargs):
        super(MoveBrutalBot, self).__init__(*args, **kwargs)
        self.from_to_pairs = from_to_pairs
        self.extras = extras
        self.page_list_output = page_list_output
        self.affected_pages = AffectedPages()

    def treat_page(self):
        self.affected_pages.add_episode(self.current_page)

        old_title = self.current_page.title()
        new_title = self._make_new_title(old_title, self.current_page)
        reason = self._single_episode_reason(old_title, new_title)

        updated_text = self.current_page.text.replace(old_title, new_title)
        extra_replacements = self.extras.get(self.current_page.title(), ())
        for old, new in extra_replacements:
            updated_text = old.sub(new, updated_text)

        self.put_current(updated_text, summary=reason)

        self.current_page.move(new_title, reason=reason, noredirect=True)

    def teardown(self):
        if self.page_list_output:
            with open(self.page_list_output, "w") as outfile:
                outfile.write(self.affected_pages.pretty_print())

        backlinks_summary = self._all_episode_reasons
        for backlink, old_pages in self.affected_pages.backlinks.items():
            new_text = backlink.text
            for old_page in old_pages:
                old_title = old_page.title()
                old_episode = self.affected_pages.files.get(old_page, old_page)
                new_title = self._make_new_title(old_title, old_episode)
                new_text = new_text.replace(old_title, new_title)

            self.userPut(backlink, backlink.text, new_text, summary=backlinks_summary)

        for file, episode in self.affected_pages.files.items():
            old_title = file.title()
            new_title = self._make_new_title(old_title, episode)
            reason = self._single_episode_reason(old_title, new_title)
            file.move(new_title, reason=reason, noredirect=True)

    def _make_new_title(self, old_title, old_episode):
        new_episode = self.from_to_pairs[old_episode]
        return old_title.replace(old_episode.title(), new_episode.title())

    @staticmethod
    def _single_episode_reason(old_title, new_title):
        return f"Move XY episodes: {old_title} -> {new_title}"

    @property
    def _all_episode_reasons(self):
        min_episode = min(self.affected_pages.episodes)
        max_episode = max(self.affected_pages.episodes)
        return f"Move XY episodes [{min_episode.title()}; {max_episode.title()}]"


def parse_extras(extras_file_name):
    extras = {}

    with open(extras_file_name, "r") as extras_file:
        for line in extras_file.readlines():
            title, *replacements = shlex.split(line.strip())
            extras[title] = [
                (re.compile(old), new)
                for old, new in itertools.batched(replacements, 2)
            ]

    return extras


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    local_args = pwb.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    from_to_pairs = {}
    page_list_output = []
    pos_args = []

    for arg in local_args:
        if not arg.startswith("-"):
            pos_args.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(":")

        match arg_name:
            case "pagesfile":
                from_to_pairs = dict(
                    itertools.batched(pagegenerators.TextIOPageGenerator(arg_value), 2)
                )

            case "output-pages-to":
                page_list_output = arg_value

            case "extras":
                extras = dict(parse_extras(arg_value))

    bot = MoveBrutalBot(
        from_to_pairs=from_to_pairs,
        extras=extras,
        generator=gen_factory.getCombinedGenerator(list(from_to_pairs.keys())),
        page_list_output=page_list_output,
    )
    bot.run()


if __name__ == "__main__":
    main()


# XY078 (https://wiki.pokemoncentral.it/XY078) nostro va spostato a XY079 e, di conseguenza, tutti quelli successivi fino a XY139 (https://wiki.pokemoncentral.it/XY139) vanno spostati di 1 in avanti
# • in tutte le pagine dove sono presenti vanno quindi sostituiti i codici con la numerazione e i titoli spostati
