import os
from typing import Optional

import mwparserfromhell
import pywikibot
from mwparserfromhell.wikicode import Wikicode

"""
Script that translates a "<Pokémon> (GCC Pokét)" from Bulba to PCW.

Arguments:
[0]: the name of the file containing the page to translate
-name:<name> the name of the Pokémon this page is for. If not given, it tries to infer
  it from the code.
"""


def apply_substitutions(source: str) -> str:
    # Dummy implementation, @lucas992x replace this
    return source


def get_name(wikicode: Wikicode, name_arg: Optional[str]) -> str:
    if name_arg is not None:
        return name_arg
    # If not provided, take the first template p it finds
    try:
        p = next(wikicode.ifilter_templates(matches=lambda t: str(t.name) == "p"))
    except StopIteration:
        raise ValueError(
            "no Pokémon name provided and can't infer from page. Aborting."
        )
    return p.params[0]


def translate_page(source: str, name_arg: Optional[str]) -> str:
    """Given the Bulbapedia page as a string, builds the PCW page."""
    source = apply_substitutions(source)
    wikicode = mwparserfromhell.parse(source, skip_style_tags=True)
    pokemon_name = get_name(wikicode, name_arg)

    # TODO from here
    return str(wikicode)


# main function
def main():
    # parse args
    local_args = pywikibot.handle_args()

    named_args = {
        "name": None,
    }
    pos_args = []
    for arg in local_args:
        if arg[0] == "-":
            arg_name, _, arg_value = arg[1:].partition(":")
            args[arg_name] = arg_value
        else:
            pos_args.append(arg.strip())

    with open(pos_args[0], "r") as f:
        source = f.read()

    print(translate_page(source, named_args["name"]))


# invoke main function
if __name__ == "__main__":
    main()
