"""Main file to extend an existing movelist."""

import logging
import sys
import os
import mwparserfromhell as mwparser
import re
from renderEntry import RenderEntry
from sourceData import get_data

logging.basicConfig(filename='../logs/extend-movelist.log',level=logging.INFO)

# Magic db source, should be retrieved given the move name
pokemon_learn = {}

def add_gen8_entry(entry_param):
    """Add a gen 8 to a single entry of a movelist render"""
    # entry = RenderEntry(entry_param)
    entry = entry_param
    if not entry.has_gen_n(8):
        if entry.get_ndex() in pokemon_learn:
            value_to_add = ", ".join(pokemon_learn[entry.get_ndex()])
            entry.add_arg(value_to_add)
        else:
            # The Pokémon can't learn the move in gen 8, so we add "no"
            entry.add_arg("no")
    return entry

def create_gen8_entry(gen, ndex, vals):
    """Create a brand new gen 8 entry.

    gen and ndex are those of the entry
    """
    entry = RenderEntry("[[€" + str(gen) + "|" + ndex + "£]]")
    for g in range(gen, 8):
        entry.add_arg("no")
    value_to_add = ", ".join(vals)
    entry.add_arg(value_to_add)
    return entry

def add_gen8(render):
    """Add gen 8 to a movelist render"""
    tmp_params = list(map(RenderEntry, render.params[2:]))
    # Update Pokémon already there
    local_mapper = lambda p: add_gen8_entry(p)
    new_params = list(map(local_mapper, tmp_params))
    # Adds new Pokémon
    curr_pokes = list(map(lambda x: x.get_ndex(), tmp_params))
    curr_gen = tmp_params[0].get_gen()
    for pk, vals in pokemon_learn.items():
        if not (pk in curr_pokes):
            new_params.append(create_gen8_entry(curr_gen, pk, vals))
    new_params.sort(key=lambda x: str(x.get_ndex()))
    render.params[2:] = map(lambda x: "\n" + str(x), new_params)
    return render

def is_render(node):
    """Check whether its argument is a render."""
    return re.match("\#invoke\:\s*render", node.name.strip().lower())

def find_first(l, f, v):
    """Return the first element of l st f(x) == v or None."""
    return next((x for x in l if f(x) == v), None)


# with open('test-sferapolline', 'r') as f:
with open('test', 'r') as f:
    ast = mwparser.parse(f.read(), skip_style_tags=True)
renders = ast.filter_templates(recursive=False,matches=is_render)

def get_render_kind(kind):
    """Return the render of the required kind or None."""
    return find_first(renders, lambda n: n.params[1].split('.')[1].strip().lower(), kind.strip().lower())

move_data = get_data("baldeali")

if __name__ == "__main__":
    pokemon_learn = move_data["level"]
    add_gen8(get_render_kind("level"))
    pokemon_learn = move_data["tm"]
    add_gen8(get_render_kind("tm"))
    print(ast)
# page = sys.stdin.read()
# ast_global = mwparser.parse(page, skip_style_tags=True)
