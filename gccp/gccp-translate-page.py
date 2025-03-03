import csv
import re
import sys
from typing import List, Optional

import mwparserfromhell
from mwparserfromhell.wikicode import Wikicode

"""
Script that translates a "<Pokémon> (GCC Pokét)" from Bulba to PCW.

Arguments:
[0]: the name of the file containing the page to translate
-name:<name> the name of the Pokémon this page is for. If not given, it tries to infer
  it from the code.
"""


def replacements_from_file(text: str, file_path: str, fields_separator=",") -> str:
    """Perform replacements reading them from a CSV.

    In the CSV, the first column is the pattern while the second is the replacement (see
    gccp-replacements.csv)"""
    # read tablewith replacements from CSV file
    with open(file_path, "r") as f:
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
    intro_template.add("1", category_name)
    # Parameter 2: expansion
    expansion = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "TCGP"))
    intro_template.add("2", expansion.get(1))
    # Parameter 3: stage
    stage = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "TCG"))
    intro_template.add("3", stage.get(1))
    # Parameter 4: type
    mon_type = next(wikicode.ifilter_templates(matches=lambda t: (t.name) == "ct"))
    intro_template.add("4", mon_type.get(1))

    return intro_template


def make_card_list_entry(wikicode: Wikicode, first: boolean) -> Wikicode:
    return ""


def make_card_list(wikicode: Wikicode) -> List[Wikicode]:
    card_list_templates = wikicode.filter_templates(matches="^{{GCCPocketCardList\/")

    card_list = []
    # Header
    card_list.append(card_list_templates[0])

    # TODO non ho capito come fare il body
    # Body
    card_list.append(make_card_list_entry())
    card_list.extend(map(make_card_list))

    # Footer
    card_list.append(card_list_templates[-1])

    return card_list


def translate_page(source: str, name_arg: Optional[str]) -> str:
    """Given the Bulbapedia page as a string, builds the PCW page."""
    source = replacements_from_file(source, "gccp-replacements.csv")
    wikicode = mwparserfromhell.parse(source, skip_style_tags=True)
    pokemon_name = get_name(wikicode, name_arg)

    # TODO from here
    # print(wikicode.get_tree())
    for node in wikicode.nodes:
        print(type(node), node)

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
    resulting_page.append(str(make_intro_template(wikicode)))

    # Make the body
    resulting_page.extend(map(str, make_card_list(wikicode)))

    # Make the interwikis
    interwikis = wikicode.ifilter_wikilinks(matches="^\[\[\w{2}:")
    interwikis = filter(lambda i: not i.startswith("[[it"), interwikis)
    # TODO add en interwiki
    resulting_page.extend(map(str, interwikis))

    return "\n".join(resulting_page)


# main function
def main():
    # parse args
    named_args = {
        "name": None,
    }
    pos_args = []
    for arg in sys.argv[1:]:
        if arg[0] == "-":
            arg_name, _, arg_value = arg[1:].partition(":")
            args[arg_name] = arg_value
        else:
            pos_args.append(arg.strip())

    with open(pos_args[0], "r") as f:
        source = f.read()

    # translate_page(source, named_args["name"])
    print("\n\n\n", translate_page(source, named_args["name"]))


# invoke main function
if __name__ == "__main__":
    main()
