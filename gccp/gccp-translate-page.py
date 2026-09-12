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


CARDLIST_HEADER = "GCCPocketCardList/Header"
CARDLIST_DIVIDER = "GCCPocketCardList/Divider"
# Bulbapedia segnala le carte -ex con questo template: va ignorato quando si
# confrontano due nomi, per capire se sono la stessa forma o due forme diverse.
EX_ICON_RE = re.compile(r"\{\{\s*ex\s*\|[^}]*\}\}", re.IGNORECASE)


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


def _template_name(template: Wikicode) -> str:
    """Nome del template, come stringa ripulita."""
    return str(template.name).strip()


def _form_key(name: str) -> str:
    """Chiave di confronto fra nomi di forma: senza il template {{ex|...}}."""
    return EX_ICON_RE.sub("", re.sub(r"\s+", " ", str(name))).strip()


def _param_text(template: Wikicode, name) -> Optional[str]:
    """Valore testuale di un parametro, o None se il parametro non c'e'."""
    if not template.has(name):
        return None
    return str(template.get(name).value).strip()


def merge_divider_into_header(rows: List[Wikicode]) -> List[Wikicode]:
    """Fonde in un unico Header un Header seguito subito da un Divider.

    Su Bulbapedia, quando la prima carta di un Pokémon appartiene a una variante
    (es. Hisuian Basculegion, Paldean Clodsire), la tabella inizia con un Header
    col nome base e subito dopo un Divider col nome della variante. Su PCW
    l'Header resterebbe senza carte sotto, mostrando una riga vuota: il nome
    dell'Header diventa quindi quello del Divider, il nome base viene
    conservato in `catname` (per la categorizzazione) e il Divider si elimina.

    Il Divider NON viene fuso quando il suo nome coincide con quello dell'Header
    (es. Header|Infernape seguito da Divider|Infernape{{ex|pocket}}): e' la
    struttura prevista dalla documentazione di Template:GCCPocketCardList/Divider
    per le sezioni -ex. Vengono inoltre saltate le intestazioni con `nocat=yes`
    (elenchi e pagine di servizio), dove l'Header e' un vero titolo di tabella.
    """
    merged: List[Wikicode] = []
    drawn: List[int] = []
    for index, row in enumerate(rows):
        if index in drawn:
            continue
        if (
            _template_name(row) == CARDLIST_HEADER
            and index + 1 < len(rows)
            and _template_name(rows[index + 1]) == CARDLIST_DIVIDER
            and not row.has("nocat")
        ):
            divider = rows[index + 1]
            base_text = _param_text(row, 1)
            variant_text = _param_text(divider, 1)
            if base_text and variant_text:
                if _form_key(variant_text) != _form_key(base_text):
                    row.add("1", variant_text)
                    row.add("catname", base_text)
                    drawn.append(index + 1)
        merged.append(row)
    return merged


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

    card_list_rows = list(
        wikicode.ifilter_templates(matches=r"^{{GCCPocketCardList\/")
    )
    # Un Header subito seguito da un Divider di forma diversa diventa un unico
    # Header: vedi merge_divider_into_header.
    card_list_rows = merge_divider_into_header(card_list_rows)

    card_list = []
    firstcard = False
    for card_list_row in card_list_rows:
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
