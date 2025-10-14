"""Run the gccp-translate-page on all files in a given directory.

Examples:
    python gccp-translate-dir.py bulbapedia-pages pcw-pages

Usage:
    python gccp-translate-dir.py [INPUT-DIR] [OUTPUT-DIR]

Arguments:
    INPUT-DIR       The directory containing the files with the Bulbapedia pages to
                    translate.

    OUTPUT-DIR      The pages where the Pokémon Central Wiki translated files will be
                    created.

Options:
    -help           Show this help text.
"""

import importlib
import os
import sys

# import gccp-translate-page module from directory of this script
gccptranslatepage = importlib.import_module("gccp-translate-page")
# import utils from 'shared' directory of this repository
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
utils_dir = os.path.join(os.path.dirname(script_dir), "shared")
spec = importlib.util.spec_from_file_location("utils", os.path.join(utils_dir, "utils.py"))  # fmt: skip
utils = importlib.util.module_from_spec(spec)
sys.modules["utils"] = utils
spec.loader.exec_module(utils)

if __name__ == "__main__":
    if "-help" in sys.argv:
        print(__doc__)
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Specify input and output dir!", file=sys.stderr)
        sys.exit(1)

    input_dir = sys.argv[1]
    if not os.path.isdir(input_dir):
        print(f"Input directory {input_dir} must exist", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[2]
    if not os.path.isdir(output_dir):
        print(f"Output directory {output_dir} must exist", file=sys.stderr)
        sys.exit(1)

    _, en_to_it, _, _, _, _, _ = utils.get_ndex_names_dicts()

    for fullname in os.listdir(path=input_dir):
        abspath = os.path.join(input_dir, fullname)
        with open(abspath, "r", encoding="utf-8") as f:
            source = f.read()

        basename = os.path.basename(fullname)
        pagename = str(basename).rsplit(".", 1)[0]
        outname = os.path.join(output_dir, utils.title_en_to_it(en_to_it, str(basename)))
        with open(outname, "w", encoding="utf-8") as out_stream:
            print(gccptranslatepage.translate_page(source, pagename), file=out_stream)
            print(f"Translated file {basename} ({pagename})")
