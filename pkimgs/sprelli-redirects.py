import argparse, sys, os, os.path, json, re
import pywikibot

"""
This script creates needed redirects for game sprites/models whose name follows
<prefix>[m|f][d][sh]<ndex>.<ext>, where
- <prefix> is abbr of game(s) preceded by "Spr"/"Icon", or just "Home"/"Mini"; for
example 'Sprnb' is for "Pokémon Nero e Bianco", "Iconlpa" is for "Leggende Pokémon: Z-A".
- [m|f] is 'f' if female and 'm' in any other case, it is not used before generation 4.
- [d] is used for back sprites/models.
- [sh] is used for shiny sprites/models.
- <ndex> is National Pokédex number, including abbr of form if applicable.
- <ext> is file extension.
Do note that a redirect is only created if destination page exists.

Arguments:
--pokeabbrs: Pokémon that need redirects, indicated as Pokédex number (on 4
digits) with form abbreviation, separated by any non-alphanumeric character. For
example "0181 0229M 0303 0303M" (without quotes) updates Ampharos, MegaHoundoom,
Mawile and MegaMawile.
--file: path of file that contains input, formatted as above; data can stay on
one line or multiple lines.
--prefixes: prefixes separated by any non-alphanumeric character (example: "Home,Mini").
--ext: extension of files (default "png").
--shiny: "no" to avoid creating redirects of shiny sprites/models (default "yes").
--back: "yes" to create redirects of back sprites/models (default "no").
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
Each item in input list should contain [prefix, [genders], side, color]:
Each item in output list will contain titles of redirect page and destination page.
Examples:
['Home', ['f', 'm'], '', '']    >   ['Homef0181.png', 'Homem0181.png']
['Home', ['m', 'f'], 'd', 'sh']  >   ['Homemdsh0478.png', 'Homefdsh0478.png']
"""  # fmt: on
def build_gender_redirects(pokeabbr, combinations):
    redirects = []
    for prefix, genders, side, color in combinations:
        redirects += [
            [
                f"{prefix}{genders[0]}{side}{color}{pokeabbr}.png",
                f"{prefix}{genders[1]}{side}{color}{pokeabbr}.png",
            ]
        ]
    return redirects


# prefixes, sides and colors are from input args; output is same as above
def build_genderform_redirects(pokeabbr, prefixes, sides, colors):
    redirects = []
    poke = re.sub(r"\D", r"", pokeabbr)
    abbr = "F"
    for prefix in prefixes:
        for side in sides:
            for color in colors:
                source = f"{prefix}f{side}{color}{poke}.png"
                dest = f"{prefix}f{side}{color}{poke}{abbr}.png"
                redirects.append([source, dest])
    for prefix in prefixes:
        for side in sides:
            for color in colors:
                source = f"{prefix}m{side}{color}{poke}{abbr}.png"
                dest = f"{prefix}f{side}{color}{poke}{abbr}.png"
                redirects.append([source, dest])
    return redirects


# fmt: off
"""
Each item in output list will contain titles of redirect page and destination page. Examples:
['Homef0181.png', 'Homem0181.png']
['Homemsh0478.png', 'Homefsh0478.png']
"""
# fmt: on
def get_needed_redirects(pokeabbr, prefixes, femaleonly=False, genderdiffs=False, genderform=False, sides=[""], colors=[""]):  # fmt: skip
    # initialize variables
    redirects = []
    # if female only, create redirects from male models to female ones
    if femaleonly:
        combinations = [
            [p, ["m", "f"], s, c] for p in prefixes for s in sides for c in colors
        ]
        redirects = build_gender_redirects(pokeabbr, combinations)
    # nothing to do with gender differences
    elif genderdiffs:
        combinations = []
        redirects = []
    # handle f and F in redirects
    elif genderform:
        combinations = []
        redirects = build_genderform_redirects(pokeabbr, prefixes, sides, colors)
    # in default case create redirects from female models to male ones (see below)
    else:
        combinations = [
            [p, ["f", "m"], s, c] for p in prefixes for s in sides for c in colors
        ]
        redirects = build_gender_redirects(pokeabbr, combinations)
    # print(combinations)
    return redirects
"""
For gender differences treated as non-useless forms, here are existing models:

Homem0678
Homemsh0678
Homef0678F
Homefsh0678F

and here are needed redirects:

Homef0678       >   Homef0678F
Homefsh0678     >   Homefsh0678F
Homem0678F      >   Homef0678F
Homemsh0678F    >   Homefsh0678F
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
    files_ns = "File:"
    for source, dest in redirects:
        if not source.startswith(files_ns):
            source = f"{files_ns}:{source}"
        if not dest.startswith(files_ns):
            dest = f"{files_ns}{dest}"
        wikicode = f"#RINVIA [[{dest}]]"
        if test_mode:
            print(f"{source}      >      {wikicode}")
        else:
            # ensure that destination page exists before creating redirect
            dest_page = pywikibot.Page(site, dest)
            if not dest_page.exists():
                print(f"Skipping because destination page does not exist: {dest}")
            else:
                page = pywikibot.Page(site, f"{source}")
                if not page.text.strip() == wikicode.strip():
                    page.text = wikicode
                    page.save("Bot: creating redirects for Pokémon sprites/models")
                else:
                    print(f"Skipping {source}")


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--pokeabbrs", default="")
    parser.add_argument("--file", default="")
    parser.add_argument("--prefixes", default="")
    parser.add_argument("--ext", default="png")
    parser.add_argument("--shiny", default="yes")
    parser.add_argument("--back", default="no")
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
    # get inputs
    pokeabbrs = re.findall(r"\d{4}[A-z]{0,2}", input)
    prefixes = re.findall(r"\w+", args.prefixes)
    if args.back.strip().lower() == "yes":
        sides = ["", "d"]
        sides_msg = "front and back"
    else:
        sides = [""]
        sides_msg = "front"
    if args.shiny.strip().lower() == "no":
        colors = [""]
        colors_msg = "regular"
    else:
        colors = ["", "sh"]
        colors_msg = "regular and shiny"
    print(
        "Creating redirects - prefixes: {} - sides: {} - colors: {} - Pokémon: {}".format(
            " ".join(prefixes), sides_msg, colors_msg, " ".join(pokeabbrs)
        )
    )
    # process
    for pokeabbr in pokeabbrs:
        ndex = int(re.sub(r"\D", r"", pokeabbr))
        ndexabbr = pokeabbr.lstrip("0")
        femaleonly = str(ndex) in gender_data["female-only"]
        genderdiffs = ndexabbr in gender_data["gender-diffs"]
        genderform = str(ndex) in gender_data["gender-forms"]
        redirects = get_needed_redirects(pokeabbr, prefixes, femaleonly, genderdiffs, genderform, sides, colors)  # fmt: skip
        create_redirects(redirects, test_mode)


# invoke main function
if __name__ == "__main__":
    main()
