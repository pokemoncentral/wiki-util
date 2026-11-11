import argparse, sys, os, os.path, json, re
import pywikibot

"""
This script creates all <ndex>.png pages, that should redirect to HOME models.

Arguments:
--pokeabbrs: Pokémon that need redirects, indicated as Pokédex number (on 4
digits) with form abbreviation, separated by any non-alphanumeric character. For
example "0181 0229M 0303 0303M" (without quotes) updates Ampharos, MegaHoundoom,
Mawile and MegaMawile.
--file: path of file that contains input, formatted as above; data can stay on
one line or multiple lines. Is ignored if --pokeabbrs is passed. Use all-pokeabbrs.txt
file in shared folder of this repository to process all Pokémon.
--genderdatafile: path of file with gender data (already populated).
--test: "no" to perform actual modifications/uploads on website, otherwise only
a preview will be printed.
--output: path where list of destinations should be written (optional).

Quick infos about variables:
- poke is Pokédex number with leading zeros and without form abbr
- pokeabbr is Pokédex number with leading zeros and with form abbr
- ndex is Pokédex number without leading zeros and without form abbr
- ndexabbr is Pokédex number without leading zeros and with form abbr

ndex is integer, others are strings. For example Alolan Vulpix has:
poke = '0037'
pokeabbr = '0037A'
ndex = 37
ndexabbr = '37A'
"""


# find destination of current pokeabbr
def find_redirect_destination(pokeabbr, gender_data):
    ndexabbr = pokeabbr.lstrip("0")
    ndex = int(re.sub(r"\D", "", ndexabbr))
    abbr = re.sub(r"\d", "", ndexabbr)
    if str(ndex) in gender_data["female-only"]:
        gender = "f"
    elif str(ndex) in gender_data["gender-forms"] and abbr == "F":
        gender = "f"
    elif str(ndex) in gender_data["gender-diffs"] and abbr == "F":
        gender = "f"
        pokeabbr = re.sub(r"\D", "", pokeabbr)
    else:
        gender = "m"
    destination = f"Home{gender}{pokeabbr}.png"
    return destination


# create/edit a redirect, but only if needed
def create_redirect(redirect, destination):
    site = pywikibot.Site()
    page = pywikibot.Page(site, redirect)
    if page.text.strip() != destination:
        page.text = destination
        page.save("Bot: managing redirects of ndexes")


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--pokeabbrs", default="")
    parser.add_argument("--file", default="")
    parser.add_argument("--genderdatafile", default="data/wiki-util-data/gender-data.json")  # fmt: skip
    parser.add_argument("--test", default="yes")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    # check if input is provided via argument or file
    if args.pokeabbrs:
        input = args.pokeabbrs
    elif args.file:
        if not os.path.isfile(args.file):
            sys.exit(f"Cannot find file {args.file}")
        with open(args.file, "r") as file:
            input = file.read()
    else:
        sys.exit("No input provided!")
    # setup
    test_mode = args.test.lower().strip() != "no"
    with open(args.genderdatafile, "r") as file:
        gender_data = json.load(file)
    # get inputs
    pokeabbrs = re.findall(r"\d{4}[A-z]{0,2}", input)
    # process all inputs
    out_data = ""
    for pokeabbr in pokeabbrs:
        # find proper destination
        redirect = f"{pokeabbr}.png"
        destination = find_redirect_destination(pokeabbr, gender_data)
        # create redirect or print its preview
        destination = f"#RINVIA [[File:{destination}]]"
        preview = f"{redirect}      >      {destination}"
        out_data = f"{out_data}{preview}\n"
        if test_mode:
            if not args.output:
                print(preview)
        else:
            create_redirect(redirect, destination)
    # save processed items in output file if specified
    if args.output:
        with open(args.output, "w") as file:
            file.write(out_data, ensure_ascii=False)


# invoke main function
if __name__ == "__main__":
    main()
