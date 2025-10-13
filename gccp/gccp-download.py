"""
Script that downloads pages to text files. Arguments:
-fam:<name> name of family in Pywikibot repository.
-enpages:<path> path where EN pages will be downloaded (optional, default data/gccp-enpages).
-itpages:<path> path where IT pages will be downloaded (optional, default data/gccp-itpages).
-overwrite:<yes|no> 'yes' to overwrite existing pages, otherwise they are skipped.
"""

import os
import os.path
import importlib
import sys

import pywikibot
from pywikibot import pagegenerators

# import utils from 'shared' directory of this repository
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
utils_dir = os.path.join(os.path.dirname(script_dir), "shared")
spec = importlib.util.spec_from_file_location("utils", os.path.join(utils_dir, "utils.py"))  # fmt: skip
utils = importlib.util.module_from_spec(spec)
sys.modules["utils"] = utils
spec.loader.exec_module(utils)


# main function
def main():
    # parse args
    local_args = pywikibot.handle_args()
    args = {
        "fam": "encypok",
        "enpages": "data/gccp-enpages",
        "itpages": "data/gccp-itpages",
        "overwrite": "no",
    }
    for arg in local_args:
        arg_name, _, arg_value = arg[1:].partition(":")
        args[arg_name] = arg_value
    # setup
    overwrite = args["overwrite"].strip().lower() == "yes"
    if not os.path.isdir(args["enpages"]):
        os.mkdir(args["enpages"])
    if not os.path.isdir(args["itpages"]):
        os.mkdir(args["itpages"])
    site_en = pywikibot.Site("en", fam=args["fam"])
    site_it = pywikibot.Site("it", fam=args["fam"])
    # get dictionary to map EN names to IT ones
    _, en_to_it, _, _, _, _, _ = utils.get_ndex_names_dicts()
    # retrieve list of EN pages and filter them
    cat_en = pywikibot.Category(site_en, "Category:TCG Pocket species by name")  # fmt: skip
    pages_en = pagegenerators.CategorizedPageGenerator(cat_en, recurse=True)
    pages_en = (p for p in pages_en if p.title().endswith(" (TCG Pocket)"))
    for page_en in pages_en:
        # ------------ [test modifications start]
        # page_en_file = os.path.join(args["enpages"], utils.fix_file_name(f"{page_en.title()}.txt"))  # fmt: skip
        # title_it = title_en_to_it(page_en.title(), en_to_it)
        # page_it_file = os.path.join(args["itpages"], utils.fix_file_name(f"{title_it}.txt"))  # fmt: skip
        # print(f"{page_en.title()} > {title_it}\n{page_en_file}\n{page_it_file}")
        # continue
        # ------------ [test modifications end]
        # retrieve EN page
        page_en_file = os.path.join(args["enpages"], utils.fix_file_name(f"{page_en.title()}.txt"))  # fmt: skip
        if not os.path.isfile(page_en_file) or overwrite:
            print(f"Downloading EN page: {page_en_file}")
            utils.download_page(page=page_en, dest_file=page_en_file)
        else:
            print(f"Skipping already existing EN page: {page_en_file}")
        # retrieve IT page if exists
        title_it = utils.title_en_to_it(page_en.title(), en_to_it)
        page_it_file = os.path.join(args["itpages"], utils.fix_file_name(f"{title_it}.txt"))  # fmt: skip
        page_it = pywikibot.Page(site_it, title_it)
        if not page_it.exists():
            print(f"Skipping missing IT page: {page_it_file}")
            # open(page_it_file, "w").close()
            continue
        if not os.path.isfile(page_it_file) or overwrite:
            print(f"Downloading IT page: {page_it_file}")
            utils.download_page(page=page_it, dest_file=page_it_file)
        else:
            print(f"Skipping already existing IT page: {page_it_file}")


# invoke main function
if __name__ == "__main__":
    main()
