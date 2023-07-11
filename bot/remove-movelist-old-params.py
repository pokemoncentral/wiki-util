#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot removes movelist old params from the specified pages.

These command line parameters can be used to specify which pages to work on:

&pagegenerator-params;
"""

import codecs
import re
import os

import mwparserfromhell as mwparser
import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot.bot import SingleSiteBot, ExistingPageBot

# This is required for the text that is shown when you run this script with the
# parameter -help.
docuReplacements = {"&pagegenerator-params;": pagegenerators.parameterHelp}


# Constants
TYPES = (
    "acciaio",
    "acqua",
    "buio",
    "coleot",
    "coleottero",
    "drago",
    "elettro",
    "erba",
    "folletto",
    "fuoco",
    "ghiaccio",
    "lotta",
    "normale",
    "psico",
    "roccia",
    "spettro",
    "terra",
    "veleno",
    "volante",
)

KINDS_WITH_GEN = ("level", "tm", "breed")


def templates_by_name(name, ast):
    """Get an iterator over templates with a specified name."""
    name = name.lower().strip()
    return ast.ifilter_templates(matches=lambda t: t.name.lower().strip() == name)


class UseOnceBot(SingleSiteBot, ExistingPageBot):
    def __init__(self, summary: str, **kwargs):
        """Initializer."""
        super(UseOnceBot, self).__init__(**kwargs)

        self.summary = summary or "Bot: removing deprecated parameters from movelist"

    def has_extra_params(self, movelist, first_param):
        """Assume there are extra params if 1 is (1|2) and 2, 3 are types."""
        return (
            len(movelist) > first_param + 4
            and movelist[first_param + 2].strip() in ("1", "2")
            and movelist[first_param + 3].strip().lower() in TYPES
            and movelist[first_param + 4].strip().lower() in TYPES
        )

    def inner_fix_line(self, line, ndex_idx):
        pieces = line.split("|")

        if self.has_extra_params(pieces, ndex_idx):
            pieces = pieces[: ndex_idx + 1] + pieces[ndex_idx + 5 :]
        return "|".join(pieces)

    def fix_movelist(self, movelist):
        """Changes the movelist inplace, removing the parameters."""
        ndex_idx = 3 if movelist.get(1).value.matches(KINDS_WITH_GEN) else 2

        # Cast to string, then process "by hand"
        line = str(movelist)

        if not line.startswith("{{") or not line.endswith("}}"):
            raise ValueError(f"This shit is not a template: {line}")

        # {{#invoke: Movelist/entry | Event |052|Meowth|1|Normale|Normale|Meowth Team Rocket||Livello 15}}
        return self.inner_fix_line(line, ndex_idx)
        # pieces = line.split("|")

        # if self.has_extra_params(pieces, ndex_idx):
        #     pieces = pieces[:ndex_idx + 1] + pieces[ndex_idx + 5:]
        # return "|".join(pieces)

    def fix_render_line(self, has_gen, line):
        # Check if the line is a render
        if not line.startswith("[[€"):
            return line
        # [[€2|137|Porygon|1|Normale|Normale|1|1|LGPE=no|25|1|1|1|25|]]|
        return self.inner_fix_line(line, 1 if has_gen else 0)

    def fix_render(self, render):
        # print(render.get(2).value)
        kind = render.get(2).value.split(".")[1].strip().lower()
        has_gen = kind in KINDS_WITH_GEN
        lines = str(render).split("\n")
        newlines = [self.fix_render_line(has_gen, line) for line in lines]
        return "\n".join(newlines)

    def treat(self, page):
        """Treats a single page.

        It looks for all movelist calls and remove the extra parameters.
        """

        # Parsing the page
        content = mwparser.parse(page.text, skip_style_tags=True)

        # First it processes all the direct calls to Movelist (not render)
        for movelist in templates_by_name("#invoke: Movelist/entry", content):
            content.replace(movelist, self.fix_movelist(movelist))

        # Then all the render
        for render in templates_by_name("#invoke: Render", content):
            content.replace(render, self.fix_render(render))

        self.userPut(
            page=page, oldtext=page.text, newtext=content, summary=self.summary
        )


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # Summary message, whether to accept all uploads
    summary, always = None, False

    genFactory = pagegenerators.GeneratorFactory()

    # Processing all global bot args
    local_args = pwb.handle_args(args)

    # Positional args
    pos_args = []

    # Processing all non-global CLI arguments
    for arg in local_args:
        if genFactory.handle_arg(arg):
            continue

        # All the arguments not starting with "-" are considered positional.
        if not arg.startswith("-"):
            pos_args.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(":")

        if arg_name == "always":
            always = True
        elif arg_name == "summary":
            summary = arg_value

    bot = UseOnceBot(
        always=always,
        summary=summary,
        generator=genFactory.getCombinedGenerator(),
    )
    bot.run()


if __name__ == "__main__":
    main()
