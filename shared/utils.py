import os
import json
import pywikibot


# utility function to remove invalid characters from file names, by replacing
# them with desired character (or an empty string to simply remove them); use
# only on a file/directory name, never on a path, where it would break
# everything by replacing path separators (/ or \)
def fix_file_name(file_name, replacement="_"):
    invalid_chars = r'<>:"/\|?*'
    for ic in invalid_chars:
        file_name = file_name.replace(ic, replacement)
    return file_name


# utility function to download wikicode from a page and save it in text file
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


# read JSON file containing Pokémon names in all languages
def read_json_names():
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    json_file_path = os.path.join(script_dir, "poke-names.json")
    with open(json_file_path, "r") as file:
        json_names = json.load(file)
    return json_names


# read poke-names.json file in this directory to get useful dictionaries
def get_ndex_names_dicts():
    # initialize empty dicts
    ndex_to_it = {}
    en_to_it = {}
    it_to_en = {}
    it_to_es = {}
    it_to_de = {}
    it_to_fr = {}
    it_to_jp = {}
    # loop over JSON to populate dicts
    json_names = read_json_names()
    for j in json_names:
        ndex_to_it.update({j["ndex"]: j["it"]})
        en_to_it.update({j["en"]: j["it"]})
        it_to_en.update({j["it"]: j["en"]})
        it_to_es.update({j["it"]: j["es"]})
        it_to_de.update({j["it"]: j["de"]})
        it_to_fr.update({j["it"]: j["fr"]})
        it_to_jp.update({j["it"]: j["jp"]})
    return ndex_to_it, en_to_it, it_to_en, it_to_es, it_to_de, it_to_fr, it_to_jp


# print warning if file is launched standalone
if __name__ == "__main__":
    print("This file contains various utilities and is not meant to be executed standalone")  # fmt: skip
