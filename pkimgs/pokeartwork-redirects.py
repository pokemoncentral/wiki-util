import argparse, re, sys, os, os.path, json
import pywikibot

"""
This script creates redirects for Pokémon artworks: for each Pokémon the "generic"
artwork 'Artwork<ndex>.png' should redirect to 'Artwork<ndex> <source>.png' with
<source> as recent as possible. Same holds for each form.

Arguments:
--pokeabbrs: Pokémon that need redirects, indicated as Pokédex number (on 4
digits) with form abbreviation, separated by any non-alphanumeric character. For
example "0181 0229M 0303 0303M" (without quotes) updates Ampharos, MegaHoundoom,
Mawile and MegaMawile.
--file: path of file that contains input, formatted as above; data can stay on
one line or multiple lines.
--artworksfile: path of file with list of all artworks (generated with pkimgs-data.py).
--artsourcesfile: path of file with sources data (already populated).
--redirectsfile: path of file with redirects data (already populated).
--test: "no" to perform actual modifications/uploads on website, otherwise only
a preview will be printed.

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


#
def get_artsources_sources(arts_data, pokeartwork_params):
    arts_sources = []
    for param in pokeartwork_params:
        sources = [
            source
            for source in arts_data
            if arts_data[source]["pokeartwork_param"] == param
        ]
        arts_sources += sources[::-1]
    return arts_sources


#
def find_redirect(pokeabbr, artworks, arts_sources, redirects_data):
    redirect = f"File:Artwork{pokeabbr}.png"
    destination = None
    # check if destination is explicitly specified
    ndexabbr = pokeabbr.lstrip("0")
    if redirects_data["forced_arts"].get(ndexabbr, None):
        destination = redirects_data["forced_arts"][ndexabbr]
    else:
        # find most recent source for destination
        for source in arts_sources:
            art = f"Artwork{pokeabbr} {source}.png"
            if art in artworks:
                destination = art
                break
    return redirect, destination


# get HOME model if no artwork is available for current form
def get_fallback_destination(pokeabbr, gender_data):
    ndexabbr = pokeabbr.lstrip("0")
    ndex = int(re.sub(r"\D", "", ndexabbr))
    abbr = re.sub(r"\d", "", ndexabbr)
    if str(ndex) in gender_data["female-only"]:
        gender = "f"
    elif str(ndex) in gender_data["gender-forms"] and abbr == "F":
        gender = "f"
    elif str(ndex) in gender_data["gender-diffs"] and abbr == "F":
        gender = "f"
        pokeabbr = ""
    else:
        gender = "m"
    destination = f"Home{gender}{pokeabbr}.png"
    return destination


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--pokeabbrs", default="")
    parser.add_argument("--file", default="")
    parser.add_argument("--artworksfile", default="data/pokepages-catlists/Artwork Pokémon.txt")  # fmt: skip
    parser.add_argument("--artsourcesfile", default="data/pokepages-utils/artsources.json")  # fmt: skip
    parser.add_argument("--redirectsfile", default="data/pokepages-utils/pokeartwork-redirects.json")  # fmt: skip
    parser.add_argument("--genderdatafile", default="data/wiki-util-data/gender-data.json")  # fmt: skip
    parser.add_argument("--test", default="yes")
    args = parser.parse_args()
    # read input files
    with open(args.artworksfile, "r") as file:
        artworks = file.read().splitlines()
    with open(args.artsourcesfile, "r") as file:
        arts_data = json.load(file)
    with open(args.redirectsfile, "r") as file:
        redirects_data = json.load(file)
    with open(args.genderdatafile, "r") as file:
        gender_data = json.load(file)
    # remove categories that should be ignored
    arts_data = {
        key: value
        for key, value in arts_data.items()
        if value["cat"] not in redirects_data["ignored_cats"]
    }
    # get sources sorted by priority
    arts_sources = get_artsources_sources(
        arts_data, redirects_data["pokeartwork_params"]
    )
    # remove specific artworks that should be ignored
    artworks = [a for a in artworks if a not in redirects_data["ignored_arts"]]
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
    # parse inputs
    pokeabbrs = re.findall(r"\d{4}[A-z]{0,2}", input)
    test_mode = args.test.lower().strip() != "no"
    # process all inputs
    for pokeabbr in pokeabbrs:
        redirect, destination = find_redirect(pokeabbr, artworks, arts_sources, redirects_data)  # fmt: skip
        if not destination:
            destination = get_fallback_destination(pokeabbr, gender_data)
        destination = f"#RINVIA [[File:{destination}]]"
        if test_mode:
            print(f"{redirect}      >      {destination}")
        else:
            site = pywikibot.Site()
            page = pywikibot.Page(site, redirect)
            if page.text.strip() != destination:
                # print(f"{pokeabbr}      >      {page.text.strip()}      >      {destination}")
                page.text = redirect
                page.save("Bot: managing redirects of Pokémon artworks")


# invoke main function
if __name__ == "__main__":
    main()
