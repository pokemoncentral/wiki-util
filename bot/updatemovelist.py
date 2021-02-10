#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to update movelists with a new generation.

Syntax:

    python pwb.py updatemovelist {<pagename>|<generator>} [<options>]

TODO

&params;
"""
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import csv
import re

from movelistlib.slpp.slpp import slpp as slpp
from movelistlib.renderentry import RenderEntry
from movelistlib.preprocess import preprocess

import mwparserfromhell as mwparser
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    ExistingPageBot, FollowRedirectPageBot, SingleSiteBot
)


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class UpdateMovelistBot(SingleSiteBot, FollowRedirectPageBot, ExistingPageBot):
    """A bot that updates movelists in a move's page."""

    # MOVE_DATA = "/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-util/"\
    #             "pokemoves-autogen/learnlist-gen/movepokes-data{gen}.lua"
    MOVE_DATA = "/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-util/"\
                "pokemoves-autogen/extend-movelist/tests/movepokes-tmp.lua"

    @staticmethod
    def is_render(node):
        """Check whether its argument is a render module."""
        return re.match("\#invoke\:\s*render", node.name.strip().lower())

    @staticmethod
    def get_render_kind(renders, kind):
        """Return the render of the required kind or None."""
        norm_kind = kind.strip().lower()
        get_key = lambda x: x.params[1].split('.')[1].strip().lower()
        return next((x for x in renders if get_key(x) == norm_kind), None)

    def __init__(self, generation, **kwargs):
        """Initializer."""
        super(UpdateMovelistBot, self).__init__(**kwargs)
        self.generation = generation
        data_path = UpdateMovelistBot.MOVE_DATA.format(gen=generation)
        with open(data_path, "r") as f:
            self.lua_data = slpp.decode(f.read())

    def update_gen_entry(self, entry, move_data):
        """Add a gen 8 to a single entry of a movelist render"""
        if entry.get_ndex_num() in move_data:
            entry.update_gen_n(self.generation, move_data[entry.get_ndex_num()])
        elif not entry.has_gen_n(self.generation):
            # The Pokémon can't learn the move in gen 8, so we add "no"
            entry.add_arg("no")
        return entry

    def create_gen_entry(self, gen, ndex, vals):
        """Create a brand new entry.

        gen and ndex are those of the entry
        """
        entry = RenderEntry("[[€" + str(gen) + "|" + str(ndex).zfill(3) + "£]]")
        for g in range(gen, self.generation):
            entry.add_arg("no")
        entry.add_arg(vals)
        return entry

    def add_gen(self, render, data):
        """Add a gen to a movelist render"""
        if render is None:
            return
        tmp_params = list(map(RenderEntry, render.params[2:]))
        # Update Pokémon already there
        local_mapper = lambda p: self.update_gen_entry(p, data)
        new_params = list(map(local_mapper, tmp_params))
        # Adds new Pokémon
        curr_pokes = list(map(lambda x: x.get_ndex_num(), tmp_params))
        curr_gen = tmp_params[0].get_gen()
        for pk, vals in data.items():
            if not (pk in curr_pokes):
                new_params.append(self.create_gen_entry(curr_gen, pk, vals))
        new_params.sort(key=lambda x: x.get_ndex())
        render.params[2:] = map(lambda x: "\n" + str(x), new_params)
        return render

    def treat_page(self):
        """Treat a single page."""
        ast = mwparser.parse(self.current_page.text, skip_style_tags=True)
        renders = ast.filter_templates(recursive=False,
                                       matches=UpdateMovelistBot.is_render)
        data = self.lua_data[self.current_page.title().lower()]
        data = preprocess(data)
        for kind in ["level", "tm", "tutor", "breed"]:
            if kind in data:
                self.add_gen(UpdateMovelistBot.get_render_kind(renders, kind),
                             data[kind])

        self.put_current(str(ast))

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
        bot = UpdateMovelistBot(8, generator=gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
