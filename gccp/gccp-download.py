"""
Download pages to text files.
"""

import os
import os.path

import pywikibot
from pywikibot import pagegenerators

from utils.PcwCliArgs import PcwCliArgs


# download wikicode from a page and save it in text file
def download_page(page=None, site=None, title="", dest_dir="", dest_file=""):
    # if a Page object is not provided, use site and title
    if not page:
        page = pywikibot.Page(site, title)
    # if path for file is not provided, use directory and page title
    if not dest_file:
        dest_file = os.path.join(dest_dir, f"{title}.txt")
    # write page text to file
    with open(dest_file, "w", encoding="utf-8") as file:
        file.write(page.text.strip() + "\n")


# convert EN title to IT
def title_en_to_it(title_en):
    # TODO: handle cases where names are different
    return title_en.replace(" (TCG Pocket)", " (GCC Pocket)")


# main function
def main():
    args = (
        PcwCliArgs(__doc__, include_pwb=True)
        .opt("fam", "name", "name of family in Pywikibot repository", default="encypok")
        .opt(
            "enpages",
            "path",
            "path where EN pages will be downloaded",
            default="data/gccp-enpages",
        )
        .opt(
            "itpages",
            "path",
            "path where IT pages will be downloaded",
            default="data/gccp-itpages",
        )
        .flag("owerwrite", "overwrite existing pages")
        .parse()
    )
    # setup
    overwrite = args["overwrite"]
    if not os.path.isdir(args["enpages"]):
        os.mkdir(args["enpages"])
    if not os.path.isdir(args["itpages"]):
        os.mkdir(args["itpages"])
    site_en = pywikibot.Site("en", fam=args["fam"])
    site_it = pywikibot.Site("it", fam=args["fam"])
    # retrieve list of EN pages and filter them
    cat_en = pywikibot.Category(site_en, "Category:Pokémon TCG Pocket species by name")  # fmt: skip
    pages_en = pagegenerators.CategorizedPageGenerator(cat_en, recurse=True)
    pages_en = (p for p in pages_en if p.title().endswith(" (TCG Pocket)"))
    for page_en in pages_en:
        # retrieve EN page
        page_en_file = os.path.join(args["enpages"], f"{page_en.title()}.txt")
        if not os.path.isfile(page_en_file) or overwrite:
            print(f"Downloading EN page: {page_en_file}")
            download_page(page=page_en, dest_file=page_en_file)
        else:
            print(f"Skipping already existing EN page: {page_en_file}")
        # retrieve IT page if exists
        title_it = title_en_to_it(page_en.title())
        page_it_file = os.path.join(args["itpages"], f"{title_it}.txt")
        page_it = pywikibot.Page(site_it, title_it)
        if not page_it.exists():
            print(f"Skipping missing IT page: {page_it_file}")
            # open(page_it_file, "w").close()
            continue
        if not os.path.isfile(page_it_file) or overwrite:
            print(f"Downloading IT page: {page_it_file}")
            download_page(page=page_it, dest_file=page_it_file)
        else:
            print(f"Skipping already existing IT page: {page_it_file}")


# invoke main function
if __name__ == "__main__":
    main()
