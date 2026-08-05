import argparse, sys, os, os.path, json, re
import pywikibot

"""
This script creates needed redirects for HOME models (both standard ones and
resized ones). Arguments:
--pokeabbrs: Pokémon that need redirects, indicated as Pokédex number (on 4
digits) with form abbreviation, separated by any non-alphanumeric character. For
example "0181 0229M 0303 0303M" (without quotes) updates Ampharos, MegaHoundoom,
Mawile and MegaMawile.
--file: path of file that contains input, formatted as above; data can stay on
one line or multiple lines.
--genderdatafile: path of file with gender data (already populated).
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


# fmt: off
"""
Each item in input list should contain [prefix, [genders], color]:
Each item in output list will contain titles of redirect page and destination page.
Examples:
['Home', ['f', 'm'], '']    >   ['Homef0181.png', 'Homem0181.png']
['Home', ['m', 'f'], 'sh']  >   ['Homemsh0478.png', 'Homefsh0478.png']
"""  # fmt: on
def build_gender_redirects(pokeabbr, combinations):
    redirects = []
    for prefix, genders, color in combinations:
        redirects += [
            [
                f"{prefix}{genders[0]}{color}{pokeabbr}.png",
                f"{prefix}{genders[1]}{color}{pokeabbr}.png",
            ]
        ]
    return redirects


# prefixes are ["Home", "Mini"], colors are ["", "sh"], output is same as above
def build_genderform_redirects(pokeabbr, prefixes, colors):
    redirects = []
    poke = re.sub(r"\D", r"", pokeabbr)
    abbr = "F"
    for prefix in prefixes:
        for color in colors:
            source = f"{prefix}f{color}{poke}.png"
            dest = f"{prefix}f{color}{poke}{abbr}.png"
            redirects.append([source, dest])
    for prefix in prefixes:
        for color in colors:
            source = f"{prefix}m{color}{poke}{abbr}.png"
            dest = f"{prefix}f{color}{poke}{abbr}.png"
            redirects.append([source, dest])
    return redirects


# fmt: off
"""
Each item in output list will contain titles of redirect page and destination page. Examples:
['Homef0181.png', 'Homem0181.png']
['Homemsh0478.png', 'Homefsh0478.png']
"""
# fmt: on
def get_needed_redirects(pokeabbr, femaleonly=False, genderdiffs=False, genderform=False):  # fmt: skip
    # initialize variables
    redirects = []
    prefixes = ["Home", "Mini"]
    colors = ["", "sh"]
    # if female only, create redirects from male models to female ones
    if femaleonly:
        combinations = [[p, ["m", "f"], c] for p in prefixes for c in colors]
        redirects = build_gender_redirects(pokeabbr, combinations)
    # nothing to do with gender differences
    elif genderdiffs:
        combinations = []
        redirects = []
    # handle f and F in redirects
    elif genderform:
        combinations = []
        redirects = build_genderform_redirects(pokeabbr, prefixes, colors)
    # in default case create redirects from female models to male ones (see below)
    else:
        combinations = [[p, ["f", "m"], c] for p in prefixes for c in colors]
        redirects = build_gender_redirects(pokeabbr, combinations)
    # print(combinations)
    return redirects
"""
For gender differences treated as non-useless forms, here are existing models:

Homem0678
Homemsh0678
Minim0678
Minimsh0678
Homef0678F
Homefsh0678F
Minif0678F
Minifsh0678F

and here are needed redirects:

Homef0678       >   Homef0678F
Homefsh0678     >   Homefsh0678F
Minif0678       >   Minif0678F
Minifsh0678     >   Minifsh0678F
Homem0678F      >   Homef0678F
Homemsh0678F    >   Homefsh0678F
Minim0678F      >   Minif0678F
Minimsh0678F    >   Minifsh0678F
"""


# fmt: off
"""
Each item in input list should contain titles of redirect page and destination
page, without "File:". Examples:
['Homef0181.png', 'Homem0181.png']
['Homemsh0478.png', 'Homefsh0478.png']
"""
# fmt: on
def create_redirects(redirects, test_mode=True):
    site = pywikibot.Site()
    for source, dest in redirects:
        wikicode = f"#RINVIA [[File:{dest}]]"
        if test_mode:
            print(f"{source}      >      {wikicode}")
        else:
            page = pywikibot.Page(site, f"File:{source}")
            if not page.text.strip() == wikicode.strip():
                page.text = wikicode
                page.save("Bot: creating redirects for HOME models")
            else:
                print(f"Skipping {source}")


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--pokeabbrs", default="")
    parser.add_argument("--file", default="")
    parser.add_argument("--genderdatafile", default="data/wiki-util-data/gender-data.json")  # fmt: skip
    parser.add_argument("--test", default="yes")
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
    # get input
    pokeabbrs = re.findall(r"\d{4}[A-z]{0,2}", input)
    print(f"Creating HOME redirects for following Pokémon: {' '.join(pokeabbrs)}")
    # process
    for pokeabbr in pokeabbrs:
        ndex = int(re.sub(r"\D", r"", pokeabbr))
        ndexabbr = pokeabbr.lstrip("0")
        femaleonly = str(ndex) in gender_data["female-only"]
        genderdiffs = ndexabbr in gender_data["gender-diffs"]
        genderform = str(ndex) in gender_data["gender-forms"]
        redirects = get_needed_redirects(pokeabbr, femaleonly, genderdiffs, genderform)
        create_redirects(redirects, test_mode)


# invoke main function
if __name__ == "__main__":
    main()
