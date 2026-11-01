"""
Script that downloads EN pages to text files. Arguments:
-fam:<name> name of family in Pywikibot repository.
-enpages:<path> path where EN pages will be downloaded (optional, default data/gccp-enpages).
-overwrite:<yes|no> 'yes' to overwrite existing pages, otherwise they are skipped.
-batch:<n> how many pages to ask to the server at once (optional, default 50).
"""

import os
import os.path
import importlib
import sys
import time

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

EN_CATEGORY = "Category:TCG Pocket species by name"
EN_SUFFIX = " (TCG Pocket)"
EN_SEARCH = 'intitle:"(TCG Pocket)"'

# some titles have characters the Windows console cannot show (Nidoran♀, Nidoran♂):
# replace them in the output instead of stopping the script
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")


# path of the text file where the EN page is saved
def en_page_file(dest_dir, title):
    return os.path.join(dest_dir, utils.fix_file_name(f"{title}.txt"))


# The EN category has a subcategory for each Pokémon, titled like the page itself
# ("Category:Abomasnow (TCG Pocket)"): reading the members of each of them costs
# one request per Pokémon (about a thousand), which is what makes the download
# slow. Returns the subcategories and the names that look like a page title.
def en_subcategories(site):
    cat = pywikibot.Category(site, EN_CATEGORY)
    subcats = {subcat.title() for subcat in cat.subcategories()}
    names = {title.split(":", 1)[1] for title in subcats}
    return subcats, names


# Titles of the EN pages: taken from the search (cheap, and the answer arrives in
# batches) and from the subcategory names, so a page not yet indexed is not lost.
def en_page_titles(site, names):
    search = pagegenerators.SearchPageGenerator(EN_SEARCH, site=site, namespaces=[0])
    titles = {page.title() for page in search}
    if not titles:
        # no search index to ask: fall back to walking the whole category tree,
        # which costs one request per Pokémon but always works
        print("Search not available: reading the category tree (slow)")
        cat = pywikibot.Category(site, EN_CATEGORY)
        pages = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
        titles = {page.title() for page in pages}
    titles |= names
    return sorted(title for title in titles if title.endswith(EN_SUFFIX))


# main function
def main():
    # parse args
    local_args = pywikibot.handle_args()
    args = {
        "fam": "encypok",
        "enpages": "data/gccp-enpages",
        "overwrite": "no",
        "batch": "50",
    }
    for arg in local_args:
        arg_name, _, arg_value = arg[1:].partition(":")
        args[arg_name] = arg_value
    # setup
    overwrite = args["overwrite"].strip().lower() == "yes"
    try:
        batch = max(1, int(args["batch"]))
    except ValueError:
        batch = 50
    os.makedirs(args["enpages"], exist_ok=True)
    started = time.perf_counter()
    site_en = pywikibot.Site("en", fam=args["fam"])
    # retrieve list of EN pages and filter them
    subcats, subcat_names = en_subcategories(site_en)
    titles = en_page_titles(site_en, subcat_names)
    already = 0
    if not overwrite:
        # pages already downloaded are not asked to the server at all
        todo = [
            title
            for title in titles
            if not os.path.isfile(en_page_file(args["enpages"], title))
        ]
        already = len(titles) - len(todo)
        titles = todo
    # the pages are asked `batch` at a time, with their text and their categories
    # (the categories tell whether the page really belongs to the EN category)
    pages = [pywikibot.Page(site_en, title) for title in titles]
    downloaded = 0
    for page_en in pagegenerators.PreloadingGenerator(
        pages, groupsize=batch, quiet=True, categories=True
    ):
        if page_en.title() not in subcat_names and not subcats & {
            cat.title() for cat in page_en.categories()
        }:
            continue
        page_en_file = en_page_file(args["enpages"], page_en.title())
        print(f"Downloading EN page: {page_en_file}")
        utils.download_page(page=page_en, dest_file=page_en_file)
        downloaded += 1
    seconds = time.perf_counter() - started
    print(
        f"Downloaded {downloaded} EN pages in {seconds:.1f} s"
        f" ({already} already present, skipped)"
    )


# invoke main function
if __name__ == "__main__":
    main()
