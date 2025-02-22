"""Rename TCG Pocket card images to Pokémon Central Wiki naming scheme.

Examples:
    python python rename-pictures-from-drive.py \\
        -drive-pictures-dir:drive-downloads/it_IT \\
        -renamed-pictures-dir:gccp-pictures/ScontroSpaziotemporale \\
        -gccp-expansion:'Scontro Spaziotemporale' \\

    python python rename-pictures-from-drive.py \\
        -drive-pictures-dir:drive-downloads/it_IT \\
        -renamed-pictures-dir:gccp/pcw \\
        -gccp-expansion:'Scontro Spaziotemporale' \\
        -failed-log:gccp/pcw/logs/ScontroSpazioTemporale-not-renamed.log

The overall functioning of the script is the following:

- Retrieve the list of cards in the expansion from the Pokémon Central Wiki page.
  \033[1;91mNOTE\033[0m: this implies that the Pokémon Central Wiki page for the
        expansion needs to be created \033[34mfirst\033[0m.

- Match the files on Google Drive with the corresponding card data as retrieved in the
  previous step. The matching is carried out by means of the card number in the
  expansion. More info below.

- Copy the file with the Pokémon Central Wiki name into the destination directory, for
  further human verification before bulk uploading (via other scripts).

Even if the Google Drive file names contain seemingly random numbers, they are actually
sequential. However, the numbering doesn't start at 1 or 0, but rather it has two
offsets, one for \033[32mPokémon cards\033[0m and one for any \033[33mother card\033[0m
category. Furthermore, the \033[34mnumbers\033[0m are somehow hidden amidst other digits
in the file name:

c\033[32mPK\033[0m_10_00\033[34m282\033[0m0_00_NAZONOKUSA_C_M_M_it_IT.png
c\033[32mPK\033[0m_10_00\033[34m283\033[0m0_00_KUSAIHANA_C_M_M_it_IT.png
---
c\033[33mTR\033[0m_10_000\033[34m32\033[0m0_00_AKAGI_U_M_M_it_IT.png
c\033[33mTR\033[0m_10_000\033[34m33\033[0m0_00_GINGADANNOSHITAPPA_U_M_M_it_IT.png

The offsets are constant in the two file name groups (Pokémon and other categories), and
are equal to \033[32m<number-in-Google-Drive-name> - <card-number-in-expansion>\033[0m.
\033[1;91mNOTE\033[0m: offsets can be \033[34mnegative\033[0m.

The image files of TCG Pocket cards should be named like in the Google Drive
directories. You should \033[1;91mdownload\033[0m the files locally first, this script
will \033[1;91mnot\033[0m do so by its own will.

Not all the files on Google Drive follow the naming scheme exactly. The few that don't
fail are skipped, and printed both on STDERR and in a log file.

Usage:
    python rename-pictures-from-drive.py -drive-pictures-dir:<dir> \\
        -renamed-pictures-dir:<dir> -gccp-expansion:<name> [-failed-log:<file>] \\
        [-picture-ext:<extension>]

Options:

-drive-pictures-dir:<dir>       The \033[94mlocal\033[0m directory where the image files
                                from Google Drive have been downloaded.

-renamed-pictures-dir:<dir>     The directory where the image files will be
                                \033[94mcopied\033[0m with the Pokémon Central Wiki
                                name. It is created if it doesn't exist.

-gccp-expansion:<name>          The name of the TCG Pocket expansion the image files
                                belong to.

-failed-log:<file>              The file where the names of the files from Google Drive
                                that failed to be renamed will be written, one per line.
                                Any directory in the file path that doesn't exist will
                                be created. \033[33mOptional\033[0m, defaults to
                                \033[32mgccp-rename-picture-failed.log\033[0m in the
                                current directory.

-picture-ext:<extension>        The extension that the image files form Google Drive
                                have. \033[33mOptional\033[0m, defaults to
                                \033[32mpng\033[0m.
"""

import os
import re
import shutil
import sys
from dataclasses import dataclass
from enum import Enum

import mwparserfromhell as mwparser
import pywikibot


class Colors:
    blue = "\033[34m"
    green = "\033[32m"
    reset = "\033[0m"
    yellow = "\033[33m"


class CardCategory(Enum):
    PKMN = "pk"
    OTHER = "tr"


@dataclass
class Card:
    number: int
    it_name: str
    category: CardCategory

    NON_PKMN_CARD_CATEGORIES = set(("Item", "Tool", "Supporter"))

    @classmethod
    def from_template_call(cls, template_call, expansion_name, extension):
        args = template_call.params

        deck_number = int(args[0].split("/")[0])
        category = (
            CardCategory.OTHER
            if str(args[2]) in cls.NON_PKMN_CARD_CATEGORIES
            else CardCategory.PKMN
        )

        name_arg = cls._parse_name_arg(args[1], expansion_name)
        it_name = "{}{}{}.{}".format(
            name_arg.replace(" ", ""),
            expansion_name.replace(" ", ""),
            deck_number,
            extension,
        )

        return cls(deck_number, it_name, category)

    @staticmethod
    def _parse_name_arg(name_arg, expansion_name):
        arg_ast = name_arg.value

        try:
            link = next(arg_ast.ifilter_wikilinks())
            return re.sub(rf"\s*\({expansion_name}\s*\d*\)$", "", str(link.title))
        except StopIteration:
            pass

        try:
            gcc_id_call = next(arg_ast.ifilter_templates(matches="GCC( |_)ID"))
            return gcc_id_call.params[1]
        except StopIteration:
            pass

        raise ValueError(f"Can't parse card name from {name_arg}")


@dataclass
class DriveFile:
    number: int
    category: CardCategory
    name: str

    @classmethod
    def from_file_name(cls, drive_file_name):
        segments = drive_file_name.split("_")

        number = int(segments[2][:-1])
        category = CardCategory(segments[0][1:].lower())

        return cls(number, category, drive_file_name)


def category_min(items, category):
    return min(item.number for item in items if item.category == category)


def rename_pictures(
    input_dir, output_dir, expansion_name, picture_ext, failed_log_file
):
    expansion_page = pywikibot.Page(pywikibot.Site(), expansion_name + " (GCC Pocket)")
    expansion_cards = [
        Card.from_template_call(entry, expansion_name, picture_ext)
        for entry in mwparser.parse(expansion_page.text).ifilter_templates(
            matches="setlist/entry"
        )
        if expansion_name in str(entry)
    ]

    drive_files = [
        DriveFile.from_file_name(file.name)
        for file in os.scandir(input_dir)
        if file.is_file() and file.name.endswith("." + picture_ext)
    ]

    offsets = {
        c: category_min(drive_files, c) - category_min(expansion_cards, c)
        for c in list(CardCategory)
    }

    expansion_cards = {card.number: card for card in expansion_cards}
    for drive_file in drive_files:
        offset = offsets[drive_file.category]

        try:
            card = expansion_cards[drive_file.number - offset]
        except KeyError:
            print(f"{Colors.yellow}{drive_file.name} not renamed{Colors.reset}")
            failed_log_file.write(drive_file.name + os.linesep)
            continue

        shutil.copy(
            os.path.join(input_dir, drive_file.name),
            os.path.join(output_dir, card.it_name),
        )
        print(
            f"Renamed {Colors.green}{card.it_name}{Colors.reset} <- {Colors.green}{drive_file.name}{Colors.reset}",
        )


def parse_args(cli_args):
    args = {
        "picture-ext": "png",
        "failed-log": os.path.abspath("gccp-rename-picture-failed.log"),
    }
    for arg in cli_args:
        name, _, value = arg[1:].partition(":")
        match name:
            case "drive-pictures-dir" | "renamed-pictures-dir" | "failed-log":
                args[name] = os.path.abspath(value)

            case "gccp-expansion" | "picture-ext":
                args[name] = value

            case "help":
                print(__doc__)
                return None

            case _:
                raise ValueError(f"Unknown CLI argument: {name}")

    required_args = set(
        ("drive-pictures-dir", "renamed-pictures-dir", "gccp-expansion")
    )
    missing_args = required_args.difference(args.keys())
    if missing_args:
        raise ValueError(f"No value give for arguments: {", ".join(missing_args)}")

    return args


def main(cli_args=None):
    args = parse_args(cli_args or sys.argv[1:])
    if args is None:
        return

    os.makedirs(args["renamed-pictures-dir"], exist_ok=True)

    os.makedirs(os.path.dirname(args["failed-log"]), exist_ok=True)
    with open(args["failed-log"], "w") as failed_log_file:
        rename_pictures(
            args["drive-pictures-dir"],
            args["renamed-pictures-dir"],
            args["gccp-expansion"],
            args["picture-ext"],
            failed_log_file,
        )


if __name__ == "__main__":
    # Enable colored output on Windows
    if os.name == "nt":
        os.system("")
    main(sys.argv[1:])
