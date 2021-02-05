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
# import sys
# import os

import mwparserfromhell as mwparser
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    ExistingPageBot, FollowRedirectPageBot, SingleSiteBot
)


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class RenderEntry:
    '''Class to represent a single render entry.'''

    @staticmethod
    def has_right_delims(s):
        return s.startswith("[[€") and s.endswith("£]]")

    def __init__(self, param_string):
        '''
        param_string can be
            - a string or something that can be transformed into it.
                In this case should be a render entry and MUST contain
                generation and ndex.
        '''
        # Make sure that param_string is a string
        param_string = str(param_string).strip()
        if not RenderEntry.has_right_delims(param_string):
            logging.error("entry string not surronded by the right delimiters:\n%s", param_string)
            raise ValueError("Entry string not surronded by the right delimiters: \"" + param_string + "\"")
        # Positional args of the entry
        self.pos_args = []
        # Named arguments of the entry
        self.named_args = {}
        for arg in param_string[3:-3].split('|'):
            i = arg.find('=')
            if i == -1:
                self.pos_args.append(arg.strip())
            else:
                self.named_args[arg[:i]] = arg[i + 1:].strip()

    def _print_named_args(self):
        res = []
        for k, v in self.named_args.items():
            res.append(str(k) + "=" + str(v))
        return '|'.join(res)

    def __str__(self):
        '''Get the string representation to be put back in the result.'''
        if self.named_args:
            return ("[[€"
                    + '|'.join(self.pos_args)
                    + '|'
                    + self._print_named_args()
                    + "£]]")
        else:
            return ("[[€"
                    + '|'.join(self.pos_args)
                    + "£]]")


    def get_gen(self):
        '''Get the gen of the entry.'''
        return int(self.pos_args[0])

    def get_ndex(self):
        '''Get the ndex of the entry.'''
        return self.pos_args[1]

    def has_gen_n(self, g):
        '''Check whether the entry has values for gen g or not.'''
        # len >= 3 + j -> has self_gen + j
        # j = g - self_gen
        if g < self.get_gen():
            return False
        return len(self.pos_args) >= 3 + g - self.get_gen()

    def add_arg(self, value, key=None):
        '''Add an arg to the entry.

        if key is specified is added with that key (possibly overriding).
        Otherwise is added as the last positional argument.
        '''
        if key:
            self.named_args[key] = value
        else:
            self.pos_args.append(value)

CSV_DIR = "/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-util/pokemoves-autogen/intermediate-outputs/movecsv/"

def get_ndex(id, name):
    """Given the id of the db and the name compute the ndex."""
    if int(id) < 10000:
        return id.zfill(3)
    else:
        try:
            abbr = re.split('(?=[A-Z])', name, maxsplit=1)[1]
            # TODO the ndex is not id.zfill(3)
            return id.zfill(3) + abbr
        except IndexError:
            logging.error("id greater than 10000 and name without abbr: " + id + " - " + name)
            raise

def level_sort_key(lvl):
    """Changes a level to its sorting key."""
    lvl = int(lvl)
    if lvl == 0:
        return 1
    if lvl == 1:
        return 0
    return lvl

def level_mapper(lvl):
    """Changes a level to its output string."""
    if int(lvl) == 0:
        return "Evo"
    return lvl

def tm_mapper(_):
    return "yes"

def get_data(move):
    """Given a move name return the data for that move."""
    with open(CSV_DIR + move.strip().lower() + ".csv", 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        all_kinds = {}
        for row in reader:
            # id(ndex), kind, game(SpSc), level(0 for other kind), poke name
            if len(row) != 5:
                logging.error("csv row has the wrong number of items: " + str(len(row)))
                raise ValueError("csv row has the wrong number of items: " + str(len(row)))
            if row[2].strip() != "SpSc":
                logging.error("csv row has the wrong game: SpSc expected, " + row[2].strip() + " got")
                raise ValueError("csv row has the wrong game: SpSc expected, " + row[2].strip() + " got")

            ndex = get_ndex(row[0].strip(), row[4].strip())
            kind = row[1].strip()
            if kind not in all_kinds:
                all_kinds[kind] = {}
            if ndex not in all_kinds[kind]:
                all_kinds[kind][ndex] = []
            all_kinds[kind][ndex].append(row[3].strip())
    # Post processing
    for k, v in all_kinds["level"].items():
        all_kinds["level"][k] = list(map(level_mapper, sorted(v, key=level_sort_key)))
    for k, v in all_kinds["tm"].items():
        all_kinds["tm"][k] = list(map(tm_mapper, v))
    return all_kinds


def is_render(node):
    """Check whether its argument is a render module."""
    return re.match("\#invoke\:\s*render", node.name.strip().lower())

def find_first(l, f, v):
    """Return the first element of l st f(x) == v or None."""
    return next((x for x in l if f(x) == v), None)

def get_render_kind(renders, kind):
    """Return the render of the required kind or None."""
    return find_first(renders, lambda n: n.params[1].split('.')[1].strip().lower(), kind.strip().lower())


class UpdateMovelistBot(SingleSiteBot, FollowRedirectPageBot, ExistingPageBot):
    """A bot that updates movelists in a move's page."""

    def __init__(self, generation, **kwargs):
        """Initializer."""
        super(UpdateMovelistBot, self).__init__(**kwargs)
        self.generation = generation

    def add_gen_entry(self, entry, move_data):
        """Add a gen 8 to a single entry of a movelist render"""
        if not entry.has_gen_n(self.generation):
            if entry.get_ndex() in move_data:
                entry.add_arg(move_data[entry.get_ndex()])
            else:
                # The Pokémon can't learn the move in gen 8, so we add "no"
                entry.add_arg("no")
        return entry

    def create_gen_entry(self, gen, ndex, vals):
        """Create a brand new entry.

        gen and ndex are those of the entry
        """
        entry = RenderEntry("[[€" + str(gen) + "|" + ndex + "£]]")
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
        local_mapper = lambda p: self.add_gen_entry(p, data)
        new_params = list(map(local_mapper, tmp_params))
        # Adds new Pokémon
        curr_pokes = list(map(lambda x: x.get_ndex(), tmp_params))
        curr_gen = tmp_params[0].get_gen()
        for pk, vals in data.items():
            if not (pk in curr_pokes):
                new_params.append(self.create_gen_entry(curr_gen, pk, vals))
        new_params.sort(key=lambda x: str(x.get_ndex()))
        render.params[2:] = map(lambda x: "\n" + str(x), new_params)
        return render

    def treat_page(self):
        """Treat a single page."""
        ast = mwparser.parse(self.current_page.text, skip_style_tags=True)
        renders = ast.filter_templates(recursive=False,matches=is_render)
        # TODO: change this to invoke some lua script that does the job
        data = get_data(self.current_page.title().lower())
        for kind in ["level", "tm", "tutor", "breed"]:
            if kind in data:
                self.add_gen(get_render_kind(renders, kind), data[kind])

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
