import csv
import itertools
import os
import re
import sys
from typing import List, Optional, Tuple

import mwparserfromhell
import pywikibot as pwb
from mwparserfromhell.wikicode import Wikicode

"""
Script that translates a "<Pokémon> (GCC Pocket)" from Bulba to PCW.

Arguments:
[0]: the name of the file containing the page to translate
-name:<name> the name of the en page (expected format is "<pokémon> (TCG Pocket)").
  Required for the en interwiki.
"""

BULBAPEDIA = None


def count_pages_in_category(cat: str) -> int:
    global BULBAPEDIA
    if BULBAPEDIA is None:
        BULBAPEDIA = pwb.Site("en")
    cat_page = pwb.page.Category(BULBAPEDIA, title=cat)
    return BULBAPEDIA.categoryinfo(cat_page)["pages"]


def replacements_from_file(text: str, file_path: str, fields_separator=",") -> str:
    """Perform replacements reading them from a CSV.

    In the CSV, the first column is the pattern while the second is the replacement (see
    gccp-replacements.csv)"""
    # read tablewith replacements from CSV file
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
    # {{GCCPocketPokémonIntro|2|Geni Supremi|Fase 2|Erba}}
    intro_template = mwparserfromhell.nodes.template.Template("GCCPocketPokémonIntro")
    # Parameter 1: expr
    number = next(
        wikicode.ifilter_templates(matches=lambda t: (t.name).startswith("#expr:"))
    )
    number_expr = number.name[len("#expr:") :]
    category_name = number_expr.split(":")[1].split("}")[0].strip()
    intro_template.add("1", count_pages_in_category(category_name) - 1)
    # Parameter 2: expansion
    expansion = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "TCGP"))
    intro_template.add("2", expansion.get(1))
    # Parameter 3: stage
    stage = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "TCG"))
    intro_template.add("3", stage.get(1))
    # Parameter 4: type
    mon_type = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "ct"))
    intro_template.add("4", mon_type.get(1))
    # Parameter 5: second type, if any
    mon_type_idx = wikicode.index(mon_type)
    if (
        isinstance(wikicode.get(mon_type_idx + 1), mwparserfromhell.nodes.text.Text)
        and wikicode.get(mon_type_idx + 1).value.strip() == "or"
        and isinstance(
            wikicode.get(mon_type_idx + 2), mwparserfromhell.nodes.template.Template
        )
    ):
        intro_template.add("5", wikicode.get(mon_type_idx + 2).get("1"))
    else:
        intro_template.add("5", "")
    # Parameter 6 and 7: energy types
    if str(mon_type.get(1)).lower().strip() == "drago":
        energy_types = list(
            itertools.islice(
                wikicode.ifilter_templates(matches=lambda t: (t.name) == "e"), 2
            )
        )
        intro_template.add("6", energy_types[0].get(1))
        intro_template.add("7", energy_types[1].get(1))

    return intro_template


def replace_ex(val: str) -> str:
    return re.sub(r"(\w+) ex", r"\g<1>-ex", val)


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
    # EX cards
    if entry.name == "GCCPocketCardList/Divider" and entry.get("1").value.contains(
        "{{TCGP Icon|ex}}"
    ):
        entry.get("1").value.replace("{{TCGP Icon|ex}}", "{{ex|pocket}}")
        if entry.has("name"):
            entry.add("name", replace_ex(str(entry.get("name").value)))
    if entry.name == "GCCPocketCardList/Card" and entry.get("cardname").value.contains(
        "{{TCGP Icon|ex}}"
    ):
        cardname_value = entry.get("cardname").value
        # {{GCC ID|Geni Supremi|Venusaur ex|4|Venusaur}} -> [[Venusaur-ex (Geni Supremi 4)|Venusaur]]
        gccid_template = next(
            cardname_value.ifilter_templates(matches=lambda t: t.name == "GCC ID")
        )
        gccid_replacement = f"[[{replace_ex(str(gccid_template.get('2')))} ({gccid_template.get('1')} {gccid_template.get('3')})|{gccid_template.get('4')}]]"
        cardname_value.replace(gccid_template, gccid_replacement)
        cardname_value.replace("{{TCGP Icon|ex}}", "{{ex|pocket}}")
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
        resulting_page.append(f"[[en:{name_arg}]]")
    interwikis = wikicode.ifilter_wikilinks(matches=r"^\[\[\w{2}:")
    interwikis = filter(lambda i: not i.startswith("[[it"), interwikis)
    resulting_page.extend(map(str, interwikis))

    return "\n".join(resulting_page)


# main function
def main():
    # parse args
    local_args = pwb.handle_args()

    named_args = {
        "name": None,
    }
    pos_args = []
    for arg in local_args:
        if arg[0] == "-":
            arg_name, _, arg_value = arg[1:].partition(":")
            named_args[arg_name] = arg_value
        else:
            pos_args.append(arg.strip())

    with open(pos_args[0], "r", encoding="utf-8") as f:
        source = f.read()

    print(translate_page(source, named_args["name"]))


# invoke main function
if __name__ == "__main__":
    main()
