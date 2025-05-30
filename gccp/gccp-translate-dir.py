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

gccptranslatepage = importlib.import_module("gccp-translate-page")

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

    for fullname in os.listdir(path=input_dir):
        abspath = os.path.join(input_dir, fullname)
        with open(abspath, "r", encoding="utf-8") as f:
            source = f.read()

        basename = os.path.basename(fullname)
        pagename = str(basename).rsplit(".", 1)[0]
        outname = os.path.join(output_dir, str(basename).replace("TCG", "GCC"))
        with open(outname, "w", encoding="utf-8") as out_stream:
            print(gccptranslatepage.translate_page(source, pagename), file=out_stream)
            print(f"Translated file {basename} ({pagename})")
