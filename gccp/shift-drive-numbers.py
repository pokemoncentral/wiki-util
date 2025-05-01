"""Shift card numbers in TCG Pocket datamine files from Google Drive

Examples:
    python shift-drive-numbers.py -drive-pictures-dir:drive-downloads/it_IT
        -card-category:pkmn -range:22-128 -by:-7

    python shift-drive-numbers.py -drive-pictures-dir:drive-downloads/it_IT
        -card-category:other -range:22-128 -by:15

The outcome of running this script is that the card numbers embedded in the picture file
names from the TCG Pockét are shifted. For example:

cPK_10_00\033[34m282\033[0m0_00_NAZONOKUSA_C_M_M_it_IT.png -> cPK_10_00\033[34m285\033[0m0_00_NAZONOKUSA_C_M_M_it_IT.png
cPK_10_00\033[34m283\033[0m0_00_KUSAIHANA_C_M_M_it_IT.png -> cPK_10_00\033[34m286\033[0m0_00_KUSAIHANA_C_M_M_it_IT.png

The cards to operate on must be specified by means of their category ("pkmn" or "other")
and their numeric range. For more information, see the documentation for the relative
options below.

This script is mostly meant to aid in fixing bad file names from the datamines, and is
mostly useful when card numbers in a large number of sequential files are off by the
same offset. The script aims by no means at fixing \033[1;31mall\033[0m bad file names,
but rather at doing the heavy lifting in the specific situation described above.

Options:

-drive-pictures-dir:<dir>       The \033[94mlocal\033[0m directory where the image files
                                from Google Drive have been downloaded.

-card-category:<category>       The category of cards to operate on. One of "pkmn" or
                                "other", for Pokémon cards and anything else
                                respectively.

-range:<range>                  The range of card numbers that should be shifted, as two
                                numbers separated by a dash (e.g. 38-94). The range
                                endpoints are \033[94mincluded\033[0m.

-by:<offset>                    The offset the card numbers should be shifted by. Can be
                                negative.

-picture-ext:<extension>        The extension that the image files form Google Drive
                                have. \033[33mOptional\033[0m, defaults to
                                \033[32mpng\033[0m.

-help                           Display this help text.
"""

import os
import re
import shutil
import sys


class Colors:
    blue = "\033[34m"
    green = "\033[32m"
    reset = "\033[0m"
    yellow = "\033[33m"


card_category_to_file_name_segment = {"pkmn": "pk", "other": "tr"}


def shift_files(directory, category, range, by, file_ext):
    beg, end = range
    file_name_regex = re.compile(rf"^c?{category.upper()}_.+\.{file_ext}$")
    files = sorted(
        file.name
        for file in os.scandir(directory)
        if file.is_file() and file_name_regex.match(file.name)
    )
    for file_name in files:
        (base_name, _) = os.path.splitext(file_name)
        number_segment = base_name.split("_")[2]

        number = int(number_segment[:-1])
        if not beg <= number <= end:
            continue

        shifted_number = number + by
        shifted_segment = "{n:0{width}}0".format(
            n=shifted_number, width=len(number_segment) - 1
        )
        shifted_file_name = file_name.replace(number_segment, shifted_segment)

        shutil.move(
            os.path.join(directory, file_name),
            os.path.join(directory, shifted_file_name),
        )
        highlighted_original = file_name.replace(
            str(number), f"{Colors.green}{number}{Colors.reset}"
        )
        highlighted_shifted = shifted_file_name.replace(
            str(shifted_number), f"{Colors.green}{shifted_number}{Colors.reset}"
        )
        print(f"Shift {highlighted_original} -> {highlighted_shifted}")


def parse_args(cli_args):
    args = {"picture-ext": "png"}
    for arg in cli_args:
        name, _, value = arg[1:].partition(":")
        match name:
            case "drive-pictures-dir":
                args[name] = os.path.abspath(value)

            case "range":
                beg, _, end = value.partition("-")
                args[name] = (int(beg), int(end))

            case "by":
                args[name] = int(value)

            case "picture-ext":
                args[name] = value

            case "card-category":
                try:
                    args[name] = card_category_to_file_name_segment[value.lower()]
                except KeyError:
                    raise ValueError(f"Unknown card category: {value}")

            case "help":
                print(__doc__)
                return None

            case _:
                raise ValueError(f"Unknown CLI argument: {name}")

    required_args = set(("drive-pictures-dir", "card-category", "range", "by"))
    missing_args = required_args.difference(args.keys())
    if missing_args:
        raise ValueError(f"No value give for arguments: {", ".join(missing_args)}")

    return args


def main(cli_args=None):
    args = parse_args(cli_args or sys.argv[1:])
    if args is None:
        return
    shift_files(
        args["drive-pictures-dir"],
        args["card-category"],
        args["range"],
        args["by"],
        args["picture-ext"],
    )


if __name__ == "__main__":
    # Enable colored output on Windows
    if os.name == "nt":
        os.system("")
    main(sys.argv[1:])
