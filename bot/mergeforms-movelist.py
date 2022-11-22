#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to merge entries for different forms that are equal.

&params;
"""
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import csv
import re

from movelistlib.renderentry import RenderEntry
from itertools import groupby

import mwparserfromhell as mwparser
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    ExistingPageBot, FollowRedirectPageBot, SingleSiteBot
)


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class CusuMovelistBot(SingleSiteBot, FollowRedirectPageBot, ExistingPageBot):
    """A bot that merge entries in a move's page."""

    @staticmethod
    def is_old_render(node):
        """Check whether its argument is an old render module."""
        return (re.match("\#invoke\:\s*render", node.name.strip().lower())
                and node.params[0].strip() == "entry")

    @staticmethod
    def get_render_kind(renders, kind):
        """Return the render of the required kind or None."""
        norm_kind = kind.strip().lower()
        get_key = lambda x: x.params[1].split('.')[1].strip().lower()
        return next((x for x in renders if get_key(x) == norm_kind), None)

    @staticmethod
    def get_base_ndex(entry):
        """Given an ndex, returns the ndex of the base form.

        entry can be either a number or a string.
        Returns a string"""
        return str(entry.get_ndex())[0:3]


    def __init__(self, **kwargs):
        """Initializer."""
        super(CusuMovelistBot, self).__init__(**kwargs)
        self.summary = "Merging equal form entries in movelist"

    def treat_render(self, render):
        """Merges entries of a single render"""
        if render is None:
            return
        tmp_params = map(
            RenderEntry, filter(lambda x: str(x).strip(), render.params[2:]))
        # Create groups of consecutive entries with the same
        # ndex (that should correspond to forms of the same Pokémon)
        # then prompt the user whether to merge them or not
        new_params = []
        for base_ndex, entries in groupby(tmp_params, key=self.get_base_ndex):
            entries = list(entries)
            if len(entries) == 1:
                do_merge = False
            else:
                pywikibot.output(
                    "Found entries sharing ndex {}".format(base_ndex))
                for entry in entries:
                    pywikibot.output(str(entry))
                do_merge = pywikibot.input_yn(
                    "Should I merge them?", default='n')
            if do_merge:
                first = entries[0]
                first.add_arg("yes", key="allforms")
                new_params.append(first)
            else:
                new_params.extend(entries)
        # Sort before printing
        new_params.sort(key=lambda x: x.get_sort_key())
        render.params[2:] = map(lambda x: "\n" + str(x), new_params)
        return render

    def treat_page(self):
        """Treat a single page."""
        ast = mwparser.parse(self.current_page.text, skip_style_tags=True)
        renders = ast.filter_templates(recursive=False,
                                       matches=self.is_old_render)
        try:
            # for kind in ["level", "tm", "breed"]:
            for kind in ["level", "tm"]:
                self.treat_render(self.get_render_kind(renders, kind))
        except ValueError:
            pywikibot.output("Page {} has problems".format(self.current_page.title()))
            raise

        self.put_current(str(ast), summary=self.summary)

def main(*args):
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()
    options = {}

    # Parse command line arguments
    for arg in local_args:
        option, sep, value = arg.partition(':')
        gen_factory.handle_arg(arg)

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        bot = CusuMovelistBot(generator=gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
