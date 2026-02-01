"""Translate a "<Pokémon> (GCC Pocket)" from Bulbapedia to Pokémon Centra Wiki

Examples:
    python gccp-translate-page.py aron-gccp.txt -name:'Aron (TCG Pocket)'

Usage:
    python gccp-translate-page.py [BULBAPEDIA-PAGE-FILE] \\
        -name:'<Pokémon> (TCG Pocket)'

Arguments:
    BULBAPEDIA-PAGE-FILE: the name of the file containing the page to translate

Options:
    -name:<name>    The name of the en page (expected format "<Pokémon> (TCG Pocket)").
                    \033[34mRequired\033[0m for the en interwiki.

    -help           Show this help text.
"""

import csv
import itertools
import os
import re
import sys
from typing import List, Optional, Tuple

import mwparserfromhell
import pywikibot as pwb
from mwparserfromhell.wikicode import Wikicode


def replacements_from_file(text: str, file_path: str, fields_separator=",") -> str:
    """Perform replacements reading them from a CSV.

    In the CSV, the first column is the pattern while the second is the replacement (see
    gccp-replacements.csv)
    """
    # read table with replacements from CSV file
    with open(
        os.path.join(os.path.dirname(__file__), file_path), "r", encoding="utf-8"
    ) as f:
        replacements = csv.reader(f, delimiter=fields_separator)
        for row in replacements:
            # skip rows where first field is empty
            if row[0]:
                pattern, replacement = row[0], row[1]
                text = re.sub(pattern, replacement, text)
    # return modified text
    return text


def get_name(wikicode: Wikicode, name_arg: Optional[str]) -> str:
    if name_arg is not None:
        if name_arg.endswith(" (TCG Pocket)"):
            return name_arg[: -len(" (TCG Pocket)")]
        else:
            return name_arg
    # If not provided, take the first template p it finds
    try:
        p = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "p"))
    except StopIteration:
        raise ValueError(
            "no Pokémon name provided and can't infer from page. Aborting."
        )
    return p.params[0]


def make_intro_template(wikicode: Wikicode) -> Wikicode:
    """Build the intro template."""
    # {{GCCPocketPokémonIntro|Geni Supremi|Fase 2|Erba}}
    intro_template = mwparserfromhell.nodes.template.Template("GCCPocketPokémonIntro")
    # Parameter 1: expr
    # number = next(
    #    wikicode.ifilter_templates(matches=lambda t: (t.name).startswith("#expr:"))
    # )
    # number_expr = number.name[len("#expr:") :]
    # category_name = number_expr.split(":")[1].split("}")[0].strip()
    # intro_template.add("1", count_pages_in_category(category_name) - 1)
    # Parameter 1: expansion
    expansion = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "TCGP"))
    intro_template.add("1", expansion.get(1))
    # Parameter 2: stage
    stage = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "TCG"))
    intro_template.add("2", stage.get(1))
    # Parameter 3: type
    mon_type = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "ct"))
    intro_template.add("3", mon_type.get(1))
    # Parameter 4: second type, if any
    mon_type_idx = wikicode.index(mon_type)
    if (
        isinstance(wikicode.get(mon_type_idx + 1), mwparserfromhell.nodes.text.Text)
        and wikicode.get(mon_type_idx + 1).value.strip() == "or"
        and isinstance(
            wikicode.get(mon_type_idx + 2), mwparserfromhell.nodes.template.Template
        )
    ):
        intro_template.add("4", wikicode.get(mon_type_idx + 2).get("1"))
    else:
        intro_template.add("4", "")
    # Parameter 5, 6 and 7: energy types
    if (
        str(intro_template.get("3").value).lower().strip() == "drago"
        or str(intro_template.get("4").value).lower().strip() == "drago"
    ):
        energy_types = list(
            itertools.islice(
                wikicode.ifilter_templates(matches=lambda t: (t.name) == "e"), 3
            )
        )
        intro_template.add("5", energy_types[0].get(1))
        if len(energy_types) > 1:
            intro_template.add("6", energy_types[1].get(1))
            if len(energy_types) > 2:
                intro_template.add("7", energy_types[2].get(1))

    return intro_template


CARDLIST_NEXT_FIRSTCARD = ["GCCPocketCardList/Header", "GCCPocketCardList/Divider"]
CARDLIST_ENTRY_UNTOUCHED = [
    "GCCPocketCardList/Header",
    "GCCPocketCardList/Footer",
    "GCCPocketCardList/Release",
]


def make_card_list_entry(
    entry: Wikicode, firstcard: bool, first_type: str, second_type: Optional[str] = None
) -> Tuple[Wikicode, bool]:
    if entry.name in CARDLIST_NEXT_FIRSTCARD:
        firstcard = True
    if entry.name in CARDLIST_ENTRY_UNTOUCHED:
        return (entry, firstcard)
    if entry.name == "GCCPocketCardList/Card" and firstcard:
        entry.add("firstcard", "yes")
        firstcard = False
    # Reset dividers types
    if entry.name == "GCCPocketCardList/Divider":
        entry.add("2", first_type)
        entry.add("3", second_type)
    return (entry, firstcard)


def make_card_list(wikicode: Wikicode) -> List[Wikicode]:
    # Get the header types
    header = next(
        wikicode.ifilter_templates(
            matches=lambda t: t.name == "GCCPocketCardList/Header"
        )
    )
    first_type = header.get("2")
    second_type = header.get("3", default=None)

    card_list = []
    firstcard = False
    for card_list_row in wikicode.ifilter_templates(matches=r"^{{GCCPocketCardList\/"):
        new_row, firstcard = make_card_list_entry(
            card_list_row, firstcard, first_type, second_type
        )
        card_list.append(new_row)

    return card_list


def translate_page(source: str, name_arg: Optional[str]) -> str:
    """Given the Bulbapedia page as a string, builds the PCW page.

    name_arg is the name of the page on Bulbapedia. If not given, the script doesn't add
    the en interwiki and tries to guess the Pokémon name from the source.
    """
    source = replacements_from_file(source, "gccp-replacements.csv")
    wikicode = mwparserfromhell.parse(source, skip_style_tags=True)
    pokemon_name = get_name(wikicode, name_arg)

    resulting_page = []
    # Make the intro
    resulting_page.append(
        str(
            next(
                wikicode.ifilter_templates(
                    matches=lambda t: t.name.strip() == "GCCPocketPokémonPrevNext"
                )
            )
        )
    )
    resulting_page.append("")
    resulting_page.append(str(make_intro_template(wikicode)))
    resulting_page.append("")

    # Make the body
    resulting_page.extend(map(str, make_card_list(wikicode)))
    resulting_page.append("")

    # Make the interwikis
    if name_arg is not None:
        name_arg = name_arg.replace("Type_ Null", "Type: Null")
        resulting_page.append(f"[[en:{name_arg}]]")
    interwikis = wikicode.ifilter_wikilinks(matches=r"^\[\[\w{2}:")
    interwikis = filter(lambda i: not i.startswith("[[it"), interwikis)
    resulting_page.extend(map(str, interwikis))

    return "\n".join(resulting_page)


# main function
def main(args=sys.argv):
    named_args = {
        "name": None,
        "output": None,
    }
    pos_args = []
    for arg in args:
        if arg.startswith("-"):
            arg_name, _, arg_value = arg[1:].partition(":")
            named_args[arg_name] = arg_value.strip() or True
        else:
            pos_args.append(arg.strip())

    if named_args["help"]:
        print(__doc__)
        return

    with open(pos_args[0], "r", encoding="utf-8") as f:
        source = f.read()

    out_stream = (
        open(named_args["output"], "w", encoding="utf-8")
        if named_args["output"] is not None
        else sys.stdout
    )
    # This can close sys.sdout. That's not a problem
    with out_stream:
        print(translate_page(source, named_args["name"]), file=out_stream)
        print(f"Translated file {pos_args[0]} ({named_args['name']})")


# invoke main function
if __name__ == "__main__":
    main()
