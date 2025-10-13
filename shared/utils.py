import os
import json
import re
import pywikibot


# utility function to remove invalid characters from file names, by replacing
# them with desired character (or an empty string to simply remove them); use
# only on a file/directory name, never on a path, where it would break
# everything by replacing path separators (/ or \)
def fix_file_name(file_name, invalids_replacement="_"):
    invalid_chars = r'<>:"/\|?*'
    for c in invalid_chars:
        file_name = file_name.replace(c, invalids_replacement)
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


# Read poke-names.json file in this directory to get useful dictionaries that map
# ndex and names in various languages. invalids_replacement is used for characters
# that are not valid for file names, they will be replaced in keys and added as
# separate entries: for example "Type: Null" will have both "Type: Null" and "Type_ Null"
# keys that lead to the same value. This is done because some scripts use Pokémon
# names as file names and the additional key allows to map existing files that have
# their invalid characters replaced.
def get_ndex_names_dicts(invalids_replacement="_"):
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
        if invalids_replacement:
            en_to_it.update({fix_file_name(j["en"]): j["it"]})
            it_to_en.update({fix_file_name(j["it"]): j["en"]})
            it_to_es.update({fix_file_name(j["it"]): j["es"]})
            it_to_de.update({fix_file_name(j["it"]): j["de"]})
            it_to_fr.update({fix_file_name(j["it"]): j["fr"]})
            it_to_jp.update({fix_file_name(j["it"]): j["jp"]})
    return ndex_to_it, en_to_it, it_to_en, it_to_es, it_to_de, it_to_fr, it_to_jp


# Convert title of an English page to Italian. If title ends with " (TCG Pocket)",
# this string is removed and will be replaced by " (GCC Pocket)". Then page title
# is searched in en_to_it dictionary to check if English title is a Pokémon name:
# in this case Italian name is used, otherwise all English Pokémon names are
# searched in English title as whole words and replaced by Italian names.
def title_en_to_it(title_en, en_to_it):
    suffix_en = " (TCG Pocket)"
    if title_en.endswith(suffix_en):
        name_en = title_en.replace(suffix_en, "")
        suffix_it = " (GCC Pocket)"
    else:
        name_en = title_en
        suffix_it = ""
    # try to get IT name from dict, if key does not exist perform all replacements
    name_it = en_to_it.get(name_en, None)
    if not name_it:
        for key in en_to_it:
            if re.search(r"\b{}\b".format(key), name_en):
                name_it = name_en.replace(key, en_to_it[key])
    title_it = f"{name_it}{suffix_it}"
    return title_it


# print warning if file is launched standalone
if __name__ == "__main__":
    print("This file contains various utilities and is not meant to be executed standalone")  # fmt: skip
