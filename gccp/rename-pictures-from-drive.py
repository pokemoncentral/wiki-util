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

-pcw-page:<name>                The name of the Pokémon Central Wiki page containing the
                                list of cards for the TCG Pocket expansion, in the same
                                format as the actual page for the expansion would.
                                \033[33mOptional\033[0m, defaults to the actual page for
                                the TCG Pocket expansion, i.e.
                                "<expansion name> (GCC Pocket)"

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
from itertools import groupby
from typing import Tuple

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
    file_name: str
    category: CardCategory

    _NON_PKMN_CARD_CATEGORIES = set(("item", "tool", "supporter"))
    _CARD_NAME_REGEX = re.compile(r"\d+.\w+$")
    _INVALID_FILE_NAME_CHARS = re.compile(r"[^\w-]")

    @property
    def group_key(self):
        return re.sub(self._CARD_NAME_REGEX, "", self.file_name)

    @classmethod
    def from_template_call(cls, template_call, expansion_name, extension):
        args = template_call.params

        deck_number = int(args[0].split("/")[0])

        name_arg = cls._parse_name_arg(args[1], expansion_name)
        it_name = "{}{}{}.{}".format(
            name_arg.replace(" ", ""),
            cls._INVALID_FILE_NAME_CHARS.sub("", expansion_name),
            deck_number,
            extension,
        )

        category = (
            CardCategory.OTHER
            if str(args[2]).lower() in cls._NON_PKMN_CARD_CATEGORIES
            else CardCategory.PKMN
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
class SameSubjectCards:
    cards: list[Card]
    name: str
    category: CardCategory
    first_number: int

    @classmethod
    def from_group(cls, group):
        name, cards = group
        cards = list(sorted(cards, key=lambda c: c.number))
        category = cards[0].category
        first_number = cards[0].number
        return cls(cards, name, category, first_number)


@dataclass
class DriveFile:
    number: int
    category: CardCategory
    group_key: Tuple[int, str]
    sort_key: Tuple[int, int]
    name: str

    def expansion_key(self, offset):
        return (self.number - offset, *self.in_packs)

    @classmethod
    def from_file_name(cls, drive_file_name):
        (file_name, _) = os.path.splitext(drive_file_name)
        segments = file_name.split("_")

        category = CardCategory(segments[0][-2:].lower())
        number = int(segments[2][:-1])
        magical_pair = (int(segments[1][0]), int(segments[3]))

        return cls(
            number, category, (number, str(category)), magical_pair, drive_file_name
        )


@dataclass
class SameSubjectDriveFile:
    files: list[DriveFile]
    number: int
    category: CardCategory

    @classmethod
    def from_group(cls, group):
        _, drive_files = group
        files = list(sorted(drive_files, key=lambda c: c.sort_key))
        number = files[0].number
        category = files[0].category
        return cls(files, number, category)


def fetch_expansion_cards(pcw_page_title, expansion_name, picture_ext):
    expansion_page = pywikibot.Page(pywikibot.Site(), pcw_page_title)
    page_wikicode = mwparser.parse(expansion_page.text)
    return [
        Card.from_template_call(entry, expansion_name, picture_ext)
        for entry in page_wikicode.ifilter_templates(matches="setlist/entry")
        if expansion_name in str(entry)
    ]


def list_drive_files(input_dir, picture_ext):
    def is_promo(file_name):
        return "_90_" in file_name

    return [
        DriveFile.from_file_name(file.name)
        for file in os.scandir(input_dir)
        if file.is_file()
        and not is_promo(file.name)
        and file.name.endswith("." + picture_ext)
    ]


def category_min(items, category):
    return min(item.number for item in items if item.category == category)


def rename_pictures(
    *,
    input_dir,
    output_dir,
    pcw_page_title,
    expansion_name,
    picture_ext,
    failed_log_file,
):
    expansion_cards = fetch_expansion_cards(pcw_page_title, expansion_name, picture_ext)
    drive_files = list_drive_files(input_dir, picture_ext)

    offsets = {
        c: category_min(drive_files, c) - category_min(expansion_cards, c)
        for c in list(CardCategory)
    }

    expansion_cards.sort(key=lambda c: c.file_name)
    expansion_cards_by_subject = {
        (sscs := SameSubjectCards.from_group(group)).first_number: sscs
        for group in groupby(expansion_cards, key=lambda c: c.group_key)
    }

    drive_files.sort(key=lambda df: df.group_key)
    drive_files_by_subject = list(
        map(
            SameSubjectDriveFile.from_group,
            groupby(drive_files, key=lambda f: f.group_key),
        )
    )

    for drive_files_for_subject in drive_files_by_subject:
        offset = offsets[drive_files_for_subject.category]
        match_key = drive_files_for_subject.number - offset
        try:
            expansion_cards_for_subject = expansion_cards_by_subject[match_key]
        except KeyError:
            for drive_file in drive_files_for_subject.files:
                print(
                    f"{Colors.yellow}{drive_file.name} not renamed. Card in PCW not found{Colors.reset}"
                )
                failed_log_file.write(f"{drive_file.name} [NO PCW CARD]{os.linesep}")
            continue

        if len(drive_files_for_subject.files) != len(expansion_cards_for_subject.cards):
            for drive_file in drive_files_for_subject.files:
                print(
                    f"{Colors.yellow}{drive_file.name} not renamed. Card in PCW not found{Colors.reset}"
                )
                failed_log_file.write(f"{drive_file.name} [NO PCW CARD]{os.linesep}")
            continue

        for drive_file, card in zip(
            drive_files_for_subject.files, expansion_cards_for_subject.cards
        ):
            shutil.copy(
                os.path.join(input_dir, drive_file.name),
                os.path.join(output_dir, card.file_name),
            )
            print(
                f"Renamed {Colors.green}{card.file_name}{Colors.reset} <- {Colors.green}{drive_file.name}{Colors.reset}",
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

            case "gccp-expansion" | "picture-ext" | "pcw-page":
                args[name] = value

            case "help":
                print(__doc__)
                return None

            case _:
                raise ValueError(f"Unknown CLI argument: {name}")

    if "pcw-page" not in args:
        args["pcw-page"] = args["gccp-expansion"] + " (GCC Pocket)"

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
            input_dir=args["drive-pictures-dir"],
            output_dir=args["renamed-pictures-dir"],
            pcw_page_title=args["pcw-page"],
            expansion_name=args["gccp-expansion"],
            picture_ext=args["picture-ext"],
            failed_log_file=failed_log_file,
        )


if __name__ == "__main__":
    # Enable colored output on Windows
    if os.name == "nt":
        os.system("")
    main(sys.argv[1:])
