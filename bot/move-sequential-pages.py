#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot is designed to moves pages with sequential titles, such as anime episodes.

For example, it has been used to move the XY episodes forwards by one, e.g.
XY078 -> XY079, XY080 -> XY081 ... XY139 -> XY140.

WARNING: Do *NOT* use this bot to move _whatever_ kind of page. Replacing backlinks to
         moved pages is implemented with a naive find-and-replace strategy, which will
         spread chaos with non-sequential page titles.

Usage:
    pwb move-sequential-pages.py scan [global-options] -movepairs:<pairs-file> \
        -output:<json-output-file>

    pwb move-sequential-pages.py do [global-options] -pages:<json-input-file> \
        -moveorder:<asc | desc> [-extrareplacements:<extra-replacements-file>]

Options for the `scan` sub command:
    -movepairs  A file containing pairs of page titles in the format [[frompage]]
                [[topage]] [[frompage]] [[topage]] ..., optionally on multiple lines

    -output     The file where the list of affected pages will be saved, usually for
                subsequent uses of the `do` sub-command.

Options for the `do` sub command:
    -pages              The file containing the list of affected pages in the same
                        format output by the `scan` sub-command, usually from a previous
                        run of this script.

    -moveorder          `ascending`|`asc` or `descending`|`desc`. Sets the order by
                        which pages are moved and inbound links replaced. It should be
                        `descending` when moving pages ahead (e.g. AB003 -> AB004),
                        `ascending` when moving backwards (e.g. CD032 -> CD031). This is
                        necessary since otherwise moving pages would fail, as the new
                        title already exists.

    -extrareplacements  A file containing extra replacement pairs for some affected
                        pages.
                        Each line starts with the page where the replacement should
                        occur, and is followed by the replacement pairs for the page.
                        The text to replace can be a regex. Fields on a line are
                        space-separated, and can be quoted via shell syntax (precisely,
                        the subset Python's shlex module supports).
                        For example:
                        "List of episodes" damn 'oopsie woopsie'
                        EF138 twenty.+ 'twenty\1'


As you can see from the usage, this bot is operated in two steps, with two different
sub-commands `scan` and `do` (as a matter of fact, it could be two separate bots).
This is so that in case anything goes wrong when you actually operate on the Wiki, you
still have the list of pages that should have been touched originally.
Talking from personal experience, reconstructing the data from the live Wiki after you
have touched only *some* of the pages can be really time-consuming.

In the first step you gather the pages to touch, via the `scan` sub-command. The
result of the search is saved to disk in JSON format. Verify that the content looks
plausible before proceeding with the next step!

In the second step you *actually* update the Wiki via the `do` sub-command. The pages
to be touched are input in the same format as the output of the `scan` command. In this
step, the input pages are moved and inbound links to them are updated. Furthermore,
touched pages and files used by them are also moved, if their title contains the title
of an input page. Last, if any extra replacements are provided, they are also applied.

For more in-depth information on the implementation details of this bot, check the
comments in the source code just below the file's docstring.
"""

#################### What does this bot do? ####################
#
# This bot moves sequential pages. It can be used to move a range of pages by a fixed
# amount (for instance backwards by two).
#
# The bot also moves pages whose title contains any of input pages titles, provided
# that it links to the initial page. For example, when moving XY122 -> XY123, Jimmy
# (XY122) -> Jimmy (XY123) will also be moved, assuming that it links XY122.
# The backlink constraint is enforced to avoid moving unrelated pages that somehow
# contain the title of any input page.
#
# Similarly, the bot moves files whose name contains any of the input page titles, but
# only if the file is used in the input page itself, or in any page linking to it. For
# instance, when moving XY104 -> XY105, if "File:WTP XY104.png" is used in XY104 then it
# is moved to "File:WTP XY105.png".
# The file-in-use constraint is in place to avoid moving unrelated files that somehow
# contain the title of any input page.
#
# Moreover, the bot also updates links to the moved pages. This is implemented with a
# naive find-and-replace strategy, which only works because sequential pages usually
# have titles following some sort of scheme containing numbers and abbreviations. Such
# titles are hardly ever accidentally embedded in content or code, so the naive strategy
# works while keeping the implementation simple.
#
# Optionally, the bot also executes extra replacements on given pages, when a file with
# such replacements is provided. The format is somehow cumbersome, but it should not be
# used for large replacements anyway. See the docstring for the -extrareplacements
# parameter for more information about the format.

#################### Implementation quirks ####################
#
# This script has two sub commands: `scan` retrieves the pages to be updated and saves
# the results to disk; `do` uses the file produced by `scan` to actually update the live
# Wiki.
# I made this decision following the long hours spent trying to recover the list of
# affected pages from a partially updated live Wiki, whenever I spotted a bug and killed
# the bot process midway through. By forcing a dump of the affected pages before doing
# anything to the live Wiki, we won't run into this problem again.
# The two sub-commands could be implemented in separate files. However, it's clearer
# that they are are highly related if they are in the same file, and it's also easier to
# share the `AffectedPages` class by keeping it all in one file.
#
# Pages are moved without leaving behind redirects, because often the current title of a
# page to be moved will become the title of another page after all the input pages have
# been moved. For example, when moving EP006 - EP010 backwards by two, we move
# EP006 -> EP004 and EP008 -> EP006. If EP006 were moved with redirect, moving EP008
# would fail, as EP006 would still exist as a redirect.
#
# Pages are moved and link replaced in ascending or descending order, depending on a
# command-line parameter. This is because when moving pages ahead, we need to operate
# by descending order, while it has to be ascending if moving backwards.
# For example, let's use a move of BW037 - BW092 forwards by three. When moving, if we
# tried to move BW037 -> BW040 before moving BW040 -> BW043 the move would fail, as
# BW040 still exists. When replacing, if we replaced BW037 -> BW040 before replacing
# BW040 -> BW043, we'd end up replacing BW037 -> BW043, which is not what we want.
# Both of these apply recursively, so we need to move pages with higher numbers first.

import itertools
import json
import re
import shlex
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import pywikibot as pwb
from pywikibot import pagegenerators, textlib
from pywikibot.bot import ExistingPageBot, SingleSiteBot


@dataclass
class AffectedPages:
    """Keep lists of pages to move and change when moving sequential pages

    Attributes:
        from_to_pairs: The (from_page -> to_page) mapping of sequential pages to be
                       moved.

        to_move: Pages to be moved, as a mapping from the page to be moved to the input
                 page used compute the new title.

        to_change: Pages where the links to pages that will be moved need to be updated.
                   A mapping from the page to be updated to the set of pages whose links
                   need to be updated.

        input_pages: The list of pages to be moved that have been explicitly input, as
                     opposed to be computed. Optional, defaults to the keys in
                     from_to_pairs.

        range: The range of sequential pages to be moved, as [min, max]. Mostly useful
               for edit summaries.
    """

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
        """Compute to_change and to_move"""
        for input_page in self.input_pages:
            pwb.info(
                f"<<green>>[INFO]<<default>> Scanning for page '{input_page.title()}'"
            )
            self._update_for_moved_page(input_page)

    def write_json(self, file_name):
        """Write the data in this object into a JSON file"""
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
        """Return the title a page should be moved to"""
        input_page = self.to_move.get(page, page)
        moved = self.from_to_pairs[input_page]
        return page.title().replace(input_page.title(), moved.title())

    @classmethod
    def from_pairs_file(cls, pairs_file):
        """Instantiate from a file with pairs of pages to be moved"""
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
        """Instantiate from a JSON file in the format produced by write_json"""
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
        # This is called recursively by _update_inbound. Don't inline.
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
        # This stops the recursion in _update_inbound
        if page in self.to_move:
            return False

        title = page.title()
        return any(input_title in title for input_title in self._input_titles)


class UpdateLinksBot(SingleSiteBot, ExistingPageBot):
    """Update links in AffectedPage.to_change

    The only reason this is a bot and not a loop is to have global pywikibot arguments
    handled for free, especially `-simulate`.
    """

    _replace_exceptions = [
        # regex for interwiki links
        re.compile(r"\[\[\w{2}:.+\]\]")
    ]

    def __init__(
        self, affected_pages, reverse_sort, extra_replacements, *args, **kwargs
    ):
        super(UpdateLinksBot, self).__init__(
            *args, generator=affected_pages.to_change.keys(), **kwargs
        )
        self.affected_pages = affected_pages
        self.summary = f"Moving pages [{'; '.join(self.affected_pages.range)}]"

        # These are only used for sorting inbound links
        self.input_page_n, self.other_page_n = (1, 0) if reverse_sort else (0, 1)
        self.reverse = reverse_sort

        self.extra_replacements = (
            self._parse_extra_replacements_file(extra_replacements)
            if extra_replacements
            else {}
        )

    def treat_page(self):
        to_change = self.current_page
        links = self.affected_pages.to_change[to_change]
        pwb.info(
            f"<<green>>[INFO]<<default>> Replace inbound links in '{to_change.title()}'"
        )

        new_text = to_change.text
        for link in sorted(links, key=self._input_first, reverse=self.reverse):
            old_title = link.title()
            new_title = self.affected_pages.get_moved_title(link)
            pwb.debug(f"Replace '{old_title}' -> '{new_title}'")
            new_text = textlib.replaceExcept(
                new_text, old_title, new_title, self._replace_exceptions
            )

        try:
            for replacement_regex, replacement in self.extra_replacements[to_change]:
                pwb.debug(
                    f"Apply extra replacement '{replacement_regex}' -> '{replacement}'"
                )
                new_text = replacement_regex.sub(replacement, new_text)
        except KeyError:
            pass

        self.userPut(to_change, to_change.text, new_text, summary=self.summary)

    def _input_first(self, page):
        n = (
            self.input_page_n
            if page in self.affected_pages.input_pages
            else self.other_page_n
        )
        return (n, page)

    @staticmethod
    def _parse_extra_replacements_file(file_name):
        pwb.debug(f"Read extra replacements from {file_name}")
        extras = {}

        with open(file_name, "r") as file:
            for line in file.readlines():
                title, *replacements = shlex.split(line.strip())
                pwb.debug(
                    f"Populate replacement for page '{title}': [{', '.join(replacements)}]"
                )
                extras[pwb.Page(pwb.Site(), title)] = [
                    (re.compile(old), new)
                    for old, new in itertools.batched(replacements, 2)
                ]

        return extras


class MoveSequentialBot(SingleSiteBot, ExistingPageBot):
    """Move pages in AffectedPage.to_move

    The only reason this is a bot and not a loop is to have global pywikibot arguments
    handled for free, especially `-simulate`.
    """

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

        pwb.info(f"<<green>>[INFO]<<default>> Move '{old_title}' -> '{new_title}'")
        from_page.move(new_title, reason=self.reason, noredirect=True)


def verify_args(args, sub_command):
    missing_arg_names = [name for name, val in args.items() if val is None]
    if missing_arg_names:
        args_pretty = ", ".join(f'"-{arg}"' for arg in missing_arg_names)
        raise ValueError(
            f"{args_pretty} argument are mandatory with '{sub_command}' sub-command"
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
    extra_replacements = None
    output = None
    pages = None
    pairs_file = None
    reverse_sort = None

    # Processing all non-global CLI arguments
    for arg in local_args:
        # All the arguments not starting with "-" are considered positional.
        if not arg.startswith("-"):
            pos_args.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(":")
        match arg_name.lower():
            case "extrareplacements":
                extra_replacements = arg_value
            case "moveorder":
                reverse_sort = arg_value.lower().startswith("desc")
            case "movepairs":
                pairs_file = arg_value
            case "output":
                output = arg_value
            case "pages":
                pages = arg_value
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
                UpdateLinksBot(affected_pages, reverse_sort, extra_replacements).run()
                MoveSequentialBot(affected_pages, reverse_sort).run()

            case _:
                raise ValueError(f"Unknown sub-command: '{pos_args[0]}'")
    except IndexError:
        raise ValueError("No sub-command given")


if __name__ == "__main__":
    main()
