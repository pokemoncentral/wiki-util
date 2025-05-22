"""Rename TCG Pocket card images to Pokémon Central Wiki naming scheme.

Examples:
    python rename-pictures-from-drive.py \\
        -drive-pictures-dir:drive-downloads/it_IT \\
        -renamed-pictures-dir:gccp-pictures/ScontroSpaziotemporale \\
        -gccp-expansion:'Scontro Spaziotemporale' \\

    python rename-pictures-from-drive.py \\
        -drive-pictures-dir:drive-downloads/it_IT \\
        -renamed-pictures-dir:gccp/pcw \\
        -gccp-expansion:'Scontro Spaziotemporale' \\
        -pcw-page:User:Lollo/Sandbox57 \\
        -bulbapedia-pictures-dir:gccp-pictures/bulbapedia/ScontroSpaziotemporale \\
        -failed-log:gccp/pcw/logs/ScontroSpazioTemporale-not-renamed.log \\
        -picture-ext:png

The core functioning of the script consists in matching the card pictures of the
expansion from the Google Drive datamines with the images from Bulbapedia, by means of a
simple pixel-by-pixel difference \033[34mof the card art\033[0m. The Bulbapedia cards
are then matched to the Pokémon Central Wiki ones by deck number.

The card list for the expansion, and their respective file names, are fetched from the
Pokémon Central Wiki and Bulbapedia pages, by parsing their content. The Bulbapedia page
is the one listed as the English interwiki in the Pokémon Central Wiki page.

Usage:
    python rename-pictures-from-drive.py -drive-pictures-dir:<dir> \\
        -renamed-pictures-dir:<dir> -gccp-expansion:<name> [-failed-log:<file>] \\
        [-picture-ext:<extension>] [-bulbapedia-pictures-dir:<dir>]

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

-bulbapedia-pictures-dir:<dir>  The directory where the card images from Bulbapedia are
                                downloaded. If a file is already present there, it won't
                                be downloaded again. \033[33mOptional\033[0m, defaults
                                to \033[32mbulbapedia-pictures\033[0m in the same parent
                                directory as the Google Drive datamine files.

-same-color-threshold:<number>  The highest value of the individual RGB components of a
                                pixel in the \033[34mcard art diff\033[0m to consider it
                                a "black pixel", e.g. the pixel in the two card art is
                                the same. \033[33mOptional\033[0m, defaults to
                                \033[32m16.6\033[0m.

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

import functools
import math
import os
import re
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from operator import attrgetter
from typing import Optional

import mwparserfromhell as mwparser
import pywikibot
from PIL import Image, ImageChops
from PIL.Image import Resampling

BULBAPEDIA_CARD_ROW = re.compile(r"\| \d{3}/\d{3} \|\| \{\{TCG ID\|")


class Colors:
    blue = "\033[34m"
    green = "\033[32m"
    reset = "\033[0m"
    yellow = "\033[33m"


class CardCategory(Enum):
    PKMN = "pk"
    OTHER = "tr"


CARD_ART_TOP_OFFSET = 46
CARD_ART_SIZE = (367, 200)
CARD_ART_BOX = (
    0,
    CARD_ART_TOP_OFFSET,
    CARD_ART_SIZE[0],
    CARD_ART_TOP_OFFSET + CARD_ART_SIZE[1],
)

ART_DIFF_MIN_SIMILAR_PIXEL = math.floor(CARD_ART_SIZE[0] * CARD_ART_SIZE[1] * 0.85)


def read_card_art(picture):
    return picture.convert("RGB").crop(CARD_ART_BOX)


@dataclass
class Card:
    deck_number: int
    category: CardCategory
    file_name: str

    sort_key = attrgetter("deck_number")

    _file_page: pywikibot.FilePage

    _NON_PKMN_CARD_CATEGORIES = set(("item", "tool", "pokémon tool", "supporter"))
    _INVALID_FILE_NAME_CHARS = re.compile(r"[^\w-]")

    def download(self, dir_name):
        dst = os.path.join(dir_name, self.file_name)
        if not os.path.exists(dst):
            print(
                f"Download {Colors.blue}{self.file_name}{Colors.reset} from bulbapedia"
            )
            self._file_page.download(dst)
        return dst

    @classmethod
    def from_template_call(cls, template_call, page, expansion_name, extension):
        args = template_call.params

        deck_number = int(args[0].split("/")[0])
        card_name = str(cls._parse_name_arg(args[1], expansion_name))
        file_name = cls._make_card_name(
            card_name, expansion_name, deck_number, extension
        )

        category = (
            CardCategory.OTHER
            if str(args[2]).lower() in cls._NON_PKMN_CARD_CATEGORIES
            else CardCategory.PKMN
        )

        file_page = pywikibot.FilePage(page.site, file_name)

        return cls(deck_number, category, file_name, file_page)

    @classmethod
    def from_table_row(cls, table_row, page, extension):
        cells = table_row.split("||")

        deck_number = int(cells[0].replace("|", "").strip().split("/")[0])

        name_cell = next(mwparser.parse(cells[1]).ifilter_templates("TCG ID"))
        card_name = str(name_cell.params[1])
        expansion_name = str(name_cell.params[0])
        file_name = cls._make_card_name(
            card_name, expansion_name, deck_number, extension
        )

        icon_cell = next(mwparser.parse(cells[2]).ifilter_templates("TCG Icon"))
        category = (
            CardCategory.OTHER
            if icon_cell.params[0].strip().lower() in cls._NON_PKMN_CARD_CATEGORIES
            else CardCategory.PKMN
        )

        file_page = pywikibot.FilePage(page.site, file_name)

        return cls(deck_number, category, file_name, file_page)

    @classmethod
    def _make_card_name(cls, card_name, expansion_name, deck_number, ext):
        name = cls._INVALID_FILE_NAME_CHARS.sub("", card_name + expansion_name)
        return f"{name}{deck_number}.{ext}"

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
    file_path: str
    category: CardCategory

    _card_art: Optional[Image.Image] = None
    _picture_size: Optional[tuple[int, int]] = None

    @classmethod
    def from_file(cls, file):
        segments = file.name.split("_")
        category = CardCategory(segments[0][-2:].lower())
        return cls(file.path, category)

    @property
    def card_art(self):
        self._populate_picture_fields()
        return self._card_art

    @property
    def picture_size(self):
        self._populate_picture_fields()
        return self._picture_size

    def _populate_picture_fields(self):
        if self._card_art is None:
            picture = Image.open(self.file_path)
            self._card_art = read_card_art(picture)
            self._picture_size = picture.size


def fetch_expansion_cards(pcw_page_title, expansion_name, picture_ext):
    print("Fetch PCW card list")
    pcw_page = pywikibot.Page(pywikibot.Site(), pcw_page_title)
    pcw_wikicode = mwparser.parse(pcw_page.text)
    pcw_cards = [
        Card.from_template_call(entry, pcw_page, expansion_name, picture_ext)
        for entry in pcw_wikicode.ifilter_templates(matches="setlist/entry")
        if expansion_name in str(entry)
    ]

    print("Fetch Bulbapedia card list")
    try:
        bulbapedia_link = next(
            link for link in pcw_page.langlinks() if link.site.code == "en"
        )
        bulbapedia_page = pywikibot.Page(bulbapedia_link)
    except StopIteration:
        raise ValueError(f"No bulbapedia interwiki found in {pcw_page_title}!")

    bulbapedia_cards = [
        Card.from_table_row(line, bulbapedia_page, picture_ext)
        for line in bulbapedia_page.text.splitlines()
        if BULBAPEDIA_CARD_ROW.search(line)
    ]

    pcw_cards.sort(key=Card.sort_key)
    bulbapedia_cards.sort(key=Card.sort_key)
    return zip(pcw_cards, bulbapedia_cards)


def is_promo_drive_file(file_name):
    return "_90_" in file_name


def list_drive_files(input_dir, picture_ext):
    return [
        DriveFile.from_file(file)
        for file in os.scandir(input_dir)
        if file.is_file()
        and not is_promo_drive_file(file.name)
        and file.name.endswith("." + picture_ext)
    ]


def is_near_black(rgb_sum_threshold, pixel):
    (r, g, b) = pixel
    return r + g + b < rgb_sum_threshold


def rename_pictures(
    *,
    input_dir,
    output_dir,
    pcw_page_title,
    expansion_name,
    bulbapedia_pictures_dir,
    failed_log_file,
    same_rgb_threshold,
    picture_ext,
):
    expansion_cards = fetch_expansion_cards(pcw_page_title, expansion_name, picture_ext)
    drive_files = list_drive_files(input_dir, picture_ext)

    drive_picture_size = drive_files[0].picture_size
    is_same_pixel = functools.partial(is_near_black, math.ceil(same_rgb_threshold * 3))

    for pcw_card, bulbapedia_card in expansion_cards:
        pcw_card_file_path = os.path.join(output_dir, pcw_card.file_name)
        if os.path.exists(pcw_card_file_path):
            print(f"{Colors.green}{pcw_card.file_name}{Colors.reset} already renamed")
            continue

        print(f"Find file for {Colors.blue}{pcw_card.file_name}{Colors.reset}")

        bulbapedia_file_name = bulbapedia_card.download(bulbapedia_pictures_dir)
        bulbapedia_art = read_card_art(
            Image.open(bulbapedia_file_name).resize(
                drive_picture_size, Resampling.NEAREST
            )
        )

        for drive_file in drive_files:
            diff = ImageChops.difference(bulbapedia_art, drive_file.card_art)
            similar_pixel_count = sum(
                1 for pixel in diff.getdata() if is_same_pixel(pixel)
            )
            if similar_pixel_count > ART_DIFF_MIN_SIMILAR_PIXEL:
                drive_file_name = os.path.basename(drive_file.file_path)
                print(
                    f"Found {Colors.green}{drive_file_name}{Colors.reset} for {Colors.green}{pcw_card.file_name}{Colors.reset}"
                )
                shutil.move(drive_file.file_path, pcw_card_file_path)
                drive_files.remove(drive_file)
                break
        else:
            print(
                f"{Colors.yellow}Can't find file for {pcw_card.file_name}{Colors.reset}"
            )
            print(pcw_card.file_name, file=failed_log_file)


def parse_args(cli_args):
    args = {
        "picture-ext": "png",
        "failed-log": os.path.abspath("gccp-rename-picture-failed.log"),
        "same-pixel-threshold": 16.6,
    }
    for arg in cli_args:
        name, _, value = arg[1:].partition(":")
        match name:
            case (
                "drive-pictures-dir"
                | "renamed-pictures-dir"
                | "bulbapedia-pictures-dir"
                | "failed-log"
            ):
                args[name] = os.path.abspath(value)

            case "gccp-expansion" | "picture-ext" | "pcw-page":
                args[name] = value

            case "same-pixel-threshold":
                args[name] = float(value)

            case "help":
                print(__doc__)
                return None

            case _:
                raise ValueError(f"Unknown CLI argument: {name}")

    if "pcw-page" not in args:
        args["pcw-page"] = args["gccp-expansion"] + " (GCC Pocket)"
    if "bulbapedia-pictures-dir" not in args:
        args["bulbapedia-pictures-dir"] = os.path.join(
            os.path.dirname(args["drive-pictures-dir"]), "bulbapedia-pictures"
        )

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
    os.makedirs(args["bulbapedia-pictures-dir"], exist_ok=True)

    os.makedirs(os.path.dirname(args["failed-log"]), exist_ok=True)
    with open(args["failed-log"], "w") as failed_log_file:
        rename_pictures(
            input_dir=args["drive-pictures-dir"],
            output_dir=args["renamed-pictures-dir"],
            pcw_page_title=args["pcw-page"],
            expansion_name=args["gccp-expansion"],
            bulbapedia_pictures_dir=args["bulbapedia-pictures-dir"],
            failed_log_file=failed_log_file,
            same_rgb_threshold=args["same-pixel-threshold"],
            picture_ext=args["picture-ext"],
        )


if __name__ == "__main__":
    # Enable colored output on Windows
    if os.name == "nt":
        os.system("")
    main(sys.argv[1:])
