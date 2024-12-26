#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot is designed to moves pages with sequential titles, such as anime episodes.

For example, it has been used to move the XY episodes forwards by one, e.g.
XY078 -> XY079, XY080 -> XY081 ... XY139 -> XY140.

WARNING: Do *NOT* use this bot to move _whatever_ kind of page. Replacing backlinks to
         moved pages is implemented with a naive find-and-replace strategy, which will
         spread chaos with non-sequential page titles.

## Mode of operation

This bot is operated in two steps, with two different commands (as a matter of fact, it
could be two separate bots). This is so that in case anything goes wrong when you
actually operate on the Wiki, you still have the list of pages that should have been
operated on originally. Talking from personal experience, reconstructing the data from
the live Wiki after you have moved and/or updated *some* of the pages can be really
time-consuming.

In the first step you gather the pages to operate on, via the `scan` sub-command. The
result of the search is saved in the file specified in the `-output` argument, in JSON
format. Verify that the content looks plausible before proceeding with the next step!

In the second step you *actually* change stuff on the Wiki, via the `do` sub-command.
The pages to be operated on are input via the `-pages` argument, whose file is in the
same JSON format output by the `scan` sub-command.

## What is carried out

This bot moves sequential pages. It can be used to move a range of pages by a fixed
amount (for instance backwards by two).

Because of this, pages are moved without leaving behind redirects, so the initial page
title can be used by another one in the same range. For example, when moving
EP006 - EP010 backwards by two, we move EP006 -> EP004 and EP008 -> EP006. If EP006 were
moved with redirect, moving EP008 would fail, as EP006 would still exist as a redirect.

Furthermore, pages are moved in ascending or descending order, based on the `-moveorder`
argument. When moving backwards, `-moveorder` should be `ascending`, while when moving
forwards it should be `descending`. This is necessary because we first need to vacate
any existing title before we can move pages. For example, when moving BW037 - BW092
forwards by three, before we can move BW037 -> BW040 we need to move BW040 -> BW043,
BW043 -> BW046, and so on, hence the need to move pages with higher numbers first.

The bot also moves pages whose title contains any of input pages titles, provided that
it links to the initial page. For example, when moving XY122 -> XY123,
"Jimmy (XY122)" -> "Jimmy (XY123)" will also be moved, assuming that it links XY122.
The backlink constraint is enforced to avoid moving unrelated pages that somehow contain
the title of any input page.

Similarly, the bot also moves files whose name contains any of the input page titles,
but only if the file is used in the input page itself, or in any page linking to it.
For instance, when moving XY104 -> XY105, if "File:WTP XY104.png" is used in XY104
then it is moved to "File:WTP XY105.png".
The file-in-use constraint is in place to avoid moving unrelated files that somehow
contain the title of any input page.

Finally, the bot also updates links to the moved pages. This is implemented with a naive
find-and-replace strategy, which only works because sequential pages usually have titles
following some sort of scheme containing numbers and abbreviations. Such titles don't
occur normally in free text or code, making the naive replacement quite safe to execute.
"""

import itertools
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import pywikibot as pwb
from pywikibot import pagegenerators, textlib
from pywikibot.bot import ExistingPageBot, SingleSiteBot


@dataclass
class AffectedPages:
    from_to_pairs: dict[pwb.Page, pwb.Page]
    to_move: dict[pwb.Page, pwb.Page]
    to_change: defaultdict[pwb.Page, set[pwb.Page]]
    input_pages: Iterable[pwb.Page] | None = None

    def __post_init__(self):
        self.input_pages = (
            self.from_to_pairs.keys() if self.input_pages is None else self.input_pages
        )
        self._input_titles = [p.title() for p in self.input_pages]
        self.range = [min(self._input_titles), max(self._input_titles)]

    def scan(self):
        for input_page in self.input_pages:
            pwb.info(
                f"<<green>>[INFO]<<default>> Scanning for page '{input_page.title()}'"
            )
            self._update_for_moved_page(input_page)

    def write_json(self, file_name):
        json_obj = {
            "from_to_pairs": {
                from_page.title(): to_page.title()
                for from_page, to_page in self.from_to_pairs.items()
            },
            "to_move": {
                from_page.title(): to_page.title()
                for from_page, to_page in self.to_move.items()
            },
            "to_change": {
                page.title(): [l.title() for l in links]
                for page, links in self.to_change.items()
            },
        }

        with open(file_name, "w") as output:
            json.dump(json_obj, output, indent=2)

    def get_moved_title(self, page):
        input_page = self.to_move.get(page, page)
        moved = self.from_to_pairs[input_page]
        return page.title().replace(input_page.title(), moved.title())

    @classmethod
    def from_pairs_file(cls, pairs_file):
        pages = pagegenerators.TextIOPageGenerator(pairs_file)
        from_to_pairs = dict(itertools.batched(pages, 2))
        input_pages = from_to_pairs.keys()

        return cls(
            from_to_pairs=from_to_pairs,
            input_pages=input_pages,
            to_move={input_page: input_page for input_page in input_pages},
            to_change=defaultdict(
                set,
                {input_page: set((input_page,)) for input_page in input_pages},
            ),
        )

    @classmethod
    def from_json(cls, json_path):
        with open(json_path, "r") as input_json:
            json_content = json.load(input_json)

        site = pwb.Site()
        from_to_pairs = {
            pwb.Page(site, from_page): pwb.Page(site, to_page)
            for from_page, to_page in json_content["from_to_pairs"].items()
        }
        to_move = {
            pwb.Page(site, from_page): pwb.Page(site, to_page)
            for from_page, to_page in json_content["to_move"].items()
        }
        to_change = {
            pwb.Page(site, page): pagegenerators.PagesFromTitlesGenerator(links)
            for page, links in json_content["to_change"].items()
        }

        return AffectedPages(from_to_pairs, to_move, to_change)

    def _update_for_moved_page(self, page):
        self._update_inbound(page, page.backlinks())
        self._update_files(page)

    def _update_inbound(self, page, inbound_pages):
        pwb.debug(f"Update inbound links to '{page.title()}'", layer="bot")
        for inbound in inbound_pages:
            self.to_change[inbound].add(page)
            if self._should_move_page(inbound):
                self.to_move[inbound] = page
                self._update_for_moved_page(inbound)

    def _update_files(self, page):
        pwb.debug(f"Update used files in '{page.title()}'", layer="bot")
        for file in page.imagelinks():
            if self._should_move_page(file):
                self.to_move[file] = page
                self._update_inbound(file, file.using_pages())

    def _should_move_page(self, page):
        if page in self.to_move:
            return False

        title = page.title()
        return any(input_title in title for input_title in self._input_titles)


class UpdateLinksBot(SingleSiteBot, ExistingPageBot):
    _replace_exceptions = [
        # regex for interwiki links
        re.compile(r"\[\[\w{2}:.+\]\]")
    ]

    def __init__(self, affected_pages, reverse_sort, *args, **kwargs):
        super(UpdateLinksBot, self).__init__(
            *args, generator=affected_pages.to_change.keys(), **kwargs
        )
        self.affected_pages = affected_pages
        self.summary = f"Moving pages [{'; '.join(self.affected_pages.range)}]"

        self.input_page_n, self.other_page_n = (1, 0) if reverse_sort else (0, 1)
        self.reverse = reverse_sort

    def treat_page(self):
        to_change = self.current_page
        links = self.affected_pages.to_change[to_change]

        new_text = to_change.text
        for link in sorted(links, key=self._input_first, reverse=self.reverse):
            new_text = textlib.replaceExcept(
                new_text,
                link.title(),
                self.affected_pages.get_moved_title(link),
                self._replace_exceptions,
            )

        pwb.info(f"<<green>>[INFO]<<default>> Replace inbound links in {to_change}")
        self.userPut(to_change, to_change.text, new_text, summary=self.summary)

    def _input_first(self, page):
        n = (
            self.input_page_n
            if page in self.affected_pages.input_pages
            else self.other_page_n
        )
        return (n, page)


class MoveSequentialBot(SingleSiteBot, ExistingPageBot):
    def __init__(self, affected_pages, reverse_sort, *args, **kwargs):
        super(MoveSequentialBot, self).__init__(
            *args,
            generator=sorted(affected_pages.to_move.keys(), reverse=reverse_sort),
            **kwargs,
        )
        self.affected_pages = affected_pages
        self.reason = f"Moving pages [{'; '.join(self.affected_pages.range)}]"

    def treat_page(self):
        from_page = self.current_page

        old_title = from_page.title()
        new_title = self.affected_pages.get_moved_title(from_page)

        pwb.info(f"<<green>>[INFO]<<default>> Move {old_title} -> {new_title}")
        from_page.move(new_title, reason=self.reason, noredirect=True)


def verify_args(args, sub_command):
    missing_arg_names = [name for name, val in args.items() if val is None]
    if missing_arg_names:
        args_pretty = ", ".join(f'"-{arg}"' for arg in missing_arg_names)
        raise ValueError(
            f'{args_pretty} argument are mandatory with "{sub_command}" sub-command'
        )


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    local_args = pwb.handle_args(args)

    # Positional args
    pos_args = []

    # Named args
    pairs_file = None
    output = None
    pages = None
    reverse_sort = None

    # Processing all non-global CLI arguments
    for arg in local_args:
        # All the arguments not starting with "-" are considered positional.
        if not arg.startswith("-"):
            pos_args.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(":")
        match arg_name.lower():
            case "movepairs":
                pairs_file = arg_value
            case "output":
                output = arg_value
            case "pages":
                pages = arg_value
            case "moveorder":
                reverse_sort = arg_value.lower().startswith("desc")
            case _:
                raise ValueError(f"Unkwnow named argument: -{arg_name}")

    try:
        match pos_args[0].lower():
            case "scan":
                verify_args({"output": output, "movepairs": pairs_file}, "scan")
                affected_pages = AffectedPages.from_pairs_file(pairs_file)
                affected_pages.scan()
                affected_pages.write_json(output)

            case "do":
                verify_args({"pages": pages, "moveorder": reverse_sort}, "do")
                affected_pages = AffectedPages.from_json(pages)
                UpdateLinksBot(affected_pages, reverse_sort).run()
                MoveSequentialBot(affected_pages, reverse_sort).run()

            case _:
                raise ValueError(f"Unknown sub-command {pos_args[0]}")
    except IndexError:
        raise ValueError("No sub-command given")


if __name__ == "__main__":
    main()
