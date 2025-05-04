"""Run the gccp-translate-page on all files in a given directory."""
import importlib
import os
import sys

gccptranslatepage = importlib.import_module("gccp-translate-page")

OUTPUT_DIR = os.path.join("desktop", "itpages")
# OUTPUT_DIR = os.path.join("/tmp", "bbbb")

if __name__ == "__main__":
    directory = sys.argv[1]
    assert os.path.isdir(directory), f"{directory} must be a directory"
    assert os.path.isdir(OUTPUT_DIR), f"No output directory {OUTPUT_DIR}: aborting!"
    for fullname in os.listdir(path=directory):
        print(fullname)
        abspath = os.path.join(directory, fullname)
        with open(abspath, "r", encoding="utf-8") as f:
            source = f.read()

        basename = os.path.basename(fullname)
        pagename = str(basename).rsplit(".", 1)[0]
        outname = os.path.join(OUTPUT_DIR, str(basename).replace("TCG", "GCC"))
        with open(outname, "w", encoding="utf-8") as out_stream:
            print(gccptranslatepage.translate_page(source, pagename), file=out_stream)
            print(f"Translated file {basename} ({pagename})")
