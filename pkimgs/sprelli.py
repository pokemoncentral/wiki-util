import pywikibot, argparse, re, os, os.path, sys, subprocess
from pywikibot import pagegenerators

"""
This script fills "Sprello" template fields: it can be used to mass upload images
in a directory or to update an entire category on Pokémon Central Wiki. Arguments:
--dir: directory with images to upload.
--cat: category with images to update (without "Categoria:").
--prefix: if uploading/updating main series images (excluding mini sprites), can
be "Spr" for sprite/models or "Icon" for mugshots.
--type: if uploading/updating main series images, can be "sprite", "modelli", "mini sprite", "mugshot".
--game: if uploading/updating main series images, specify game/generation.
--gameabbr: if uploading/updating main series images (excluding mini sprites),
specify abbreviation of game (is lowercase and may be differ from Modulo:Sigle/data).
--ani: if uploading/updating main series images (excluding mini sprites), can be "yes" or "no".
--credits: credits for images (wikicode, optional).
--test: "no" to perform actual modifications/uploads on website, otherwise only
a preview will be printed.

In all file names mentioned in following comments it holds that:
- <...> indicates something variable, for example <ndex> is National Pokédex number.
- [...] indicates something that may be present or not.
- | indicates alternative among two or more options.

Supported games:
- Main series games (sprites, models, icons and mini sprites).
- Pokémon HOME (both standard and resized).
- Pokémon GO.
- Pokémon Sleep.
- Pokémon Masters EX.
"""


# fmt: off
"""
Get data for sprites, models and icons in main series games (NOT mini sprites).
File name is "[Spr|Icon]<game>[m|f][d][sh]<ndex>.<ext>", where:
- [Spr|Icon] is 'Spr' for sprites and models, 'Icon' for mugshots.
- <game> is abbr of game(s), for example 'nb' is for "Pokémon Nero e Bianco".
- [m|f] is 'f' if female and 'm' in any other case, it is not used before generation 4.
- [d] is used for back sprites/models.
- [sh] is used for shiny sprites/models.
- <ndex> is National Pokédex number, including abbr of form if applicable.
- <ext> is file extension.
"""  # fmt: on
def get_data_main(img, prefix, gameabbr):
    ndex = re.sub(prefix + r"\w+[mf]d?(sh)?(\d+(\w+)?)\.\w+", r"\2", img)
    if re.search(f"^{prefix}{gameabbr}[mf]?d?sh", img):
        shiny = "yes"
    else:
        shiny = "no"
    if re.search(f"^{prefix}{gameabbr}f", img):
        female = "yes"
    else:
        female = "no"
    if prefix == "Spr" and not gameabbr.startswith("dex"):
        if re.search(f"^{prefix}{gameabbr}[mf]?d", img):
            back = "yes"
        else:
            back = "no"
    else:
        back = ""
    if re.search(r"[A-z]", ndex):
        altform = "yes"
    else:
        altform = "no"
    return ndex, back, shiny, female, altform


# fmt: off
"""
Get data for main series mini sprites. File name is
"[Ani]<ndex>MS<gen|game>[OW*[sh]].<ext>", where:
- [Ani] is used for animated mini sprites.
- <ndex> works as above, except generation 1/2 where is name of a Pokémon (many
of them shared same mini sprite).
- <gen|game> is last generation or game where it is used.
- [OW*[sh]] is only used for partner Pokémon in HGSS.
- <ext> is file extension, png for static mini sprites and gif for animated ones.

AniClefairyMS1.gif
AniClefairyMS2.gif
0001MS4OWEsh.gif
Ani0001MS5.gif
0001MS5.png
0001MS7.png
0001MS.png
0001MSDLPS.png
"""  # fmt: on
def get_data_ms(img):
    type = "mini sprite"
    ndex = re.sub(r"^(Ani)?(.+?)MS.+$", r"\2", img)
    if re.search(r"^[A-z]", ndex):
        ndex = "0000"
    if img.startswith("Ani"):
        ani = "yes"
    else:
        ani = "no"
    if "MS4OW" in img:
        if re.search(r"sh\.\w+$", img):
            shiny = "yes"
        else:
            shiny = "no"
    else:
        shiny = ""
    if re.search(r"[A-z]", ndex):
        altform = "yes"
    else:
        altform = "no"
    return type, ndex, ani, shiny, altform


# fmt: off
"""
Get data for HOME models (both standard and resized). File name is
"<Home|Mini>[m|f][d][sh]<ndex>.png", where:
- <Home|Mini> is for standard and resized models respectively.
- [m|f] works as above.
- [d] is used for back models.
- [sh] works as above.
- <ndex> works as above.
"""  # fmt: on
def get_data_home(img):
    if img.startswith("Home"):
        type = "modelli"
        ani = "no"
        if re.search(r"(Home|Mini)[mf]d", img):
            back = "yes"
        else:
            back = "no"
    else:
        type = "modelli scalati"
        ani = ""
        back = ""  # resized models are only static and frontal
    ndex = re.sub(r"^[A-z]+(\d+\w*)([ _]r)?\.\w+", r"\1", img)
    if "sh" in img:
        shiny = "yes"
    else:
        shiny = "no"
    if img[4] == "f":
        female = "yes"
    else:
        female = "no"
    if re.search(r"[A-z]", ndex):
        altform = "yes"
    else:
        altform = "no"
    return type, ndex, ani, back, shiny, female, altform


# fmt: off
"""
Get data for GO models. File name is "GO<ndex>[ <event>][ f][ s].png", where:
- <ndex> works as above.
- <event> is special event, for example "FashionWeek21" or "Clone".
- [ f] is used for female models.
- [ s] is used for shiny models.
"""  # fmt: on
def get_data_go(img):
    type = "modelli"
    ndex = re.sub(r"^GO(\d+\w*)[ \.].+$", r"\1", img)
    if re.search(r" s\b", img):
        shiny = "yes"
    else:
        shiny = "no"
    if re.search(r" f\b", img):
        female = "yes"
    else:
        female = "no"
    if re.search(r"[A-z]", ndex):
        altform = "yes"
    else:
        altform = "no"
    if re.search(r"^GO(\d+\w*) \w{2,}", img):
        event = "yes"
    else:
        event = "no"
    return type, ndex, shiny, female, altform, event


# fmt: off
"""
Get data for Sleep sprite/models. File name is "Sleep<type>[sh]<ndex>[-<event>-<form>].png", where:
- <type> is "Icona" for mugshots and "Sonno" for sleep styles.
- [sh] is used for shiny sprite/models.
- <ndex> works as above.
- <event> and <form> are used for event-exclusive variants, using in-app names formatted
in Pascal Case: examples are "-Halloween-Arancione" and "-Feste-GhirlandaFestiva".
"""  # fmt: on
def get_data_sleep(img):
    if img.startswith("SleepIcona"):
        type = "mugshot"
    elif img.startswith("SleepSonno"):
        type = "sprite stili di sonno"
    ndex = re.sub(r"^[A-z]+(\d+\w*)[ \.\-].+$", r"\1", img)
    if re.search(r"sh\d{4}", img):
        shiny = "yes"
    else:
        shiny = "no"
    if re.search(r"[A-z]", ndex):
        altform = "yes"
    else:
        altform = "no"
    if re.search(r"-\w+-\w+", img):
        event = "yes"
    else:
        event = "no"
    return type, ndex, shiny, altform, event


# fmt: off
"""
Get data for Masters sprite/models. File name is "MastersEX[sh]<ndex>[f].png"
or "MastersIcona[sh]<ndex>[ f].png", where:
- [sh] is used for shiny sprite/models.
- [f] and [ f] are used for female sprite/models.
- <ndex> works as above.
"""  # fmt: on
def get_data_masters(img):
    if img.startswith("MastersIcona"):
        type = "mugshot"
    elif img.startswith("MastersEX"):
        type = "modelli"
    ndex = re.sub(r"^[A-z]+(\d+\w*)[ \.\-].+$", r"\1", img)
    if re.search(r"sh\d{4}", img):
        shiny = "yes"
    else:
        shiny = "no"
    if re.search(r"\d{4}f$", ndex) or re.search(r" f\b", img):
        female = "yes"
    else:
        female = "no"
    if re.search(r"[A-Z][A-z]?", ndex):
        altform = "yes"
    else:
        altform = "no"
    return type, ndex, shiny, female, altform


# build appropriate template
def build_template(img, prefix, type, game, gameabbr, ani, credits):
    # initialize variables to avoid errors
    back = None
    shiny = None
    female = None
    altform = None
    event = None
    # detect type, game and other info
    if prefix in ["Spr", "Icon"]:
        # type and game must be specified in these cases
        ndex, back, shiny, female, altform = get_data_main(img, prefix, gameabbr)
    elif type == "mini sprite":
        # game must be specified in these cases
        type, ndex, ani, shiny, altform = get_data_ms(img)
    elif re.search(r"^(Home|Mini)[mf]", img):
        game = "Pokémon HOME"
        type, ndex, ani, back, shiny, female, altform = get_data_home(img)
    elif img.startswith("GO"):
        game = "Pokémon GO"
        type, ndex, shiny, female, altform, event = get_data_go(img)
    elif img.startswith("Sleep"):
        game = "Pokémon Sleep"
        type, ndex, shiny, altform, event = get_data_sleep(img)
    elif img.startswith("Masters"):
        game = "Pokémon Masters EX"
        type, ndex, shiny, female, altform = get_data_masters(img)
    # build template with retrieved info
    template = f"{{{{sprello|type={type}|ndex={ndex}|game={game}"
    if ani:
        template += f"|ani={ani}"
    if back:
        template += f"|back={back}"
    if shiny:
        template += f"|shiny={shiny}"
    if female:
        template += f"|female={female}"
    if altform:
        template += f"|altform={altform}"
    if event:
        template += f"|event={event}"
    if credits:
        template += f"|credits={credits}"
    template += "}}"
    return template


# main function
def main():
    site = pywikibot.Site()
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="")
    parser.add_argument("--cat", default="")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--type", default="")
    parser.add_argument("--game", default="")
    parser.add_argument("--gameabbr", default="")
    parser.add_argument("--ani", default="")
    parser.add_argument("--credits", default="")
    parser.add_argument("--test", default="yes")
    args = parser.parse_args()
    # check arguments
    if args.dir and not os.path.isdir(args.dir):
        sys.exit(f'Error: directory "{args.dir}" not found!')
    if args.prefix in ["Spr", "Icon"]:
        if not args.type:
            sys.exit(f'Error: argument "type" not provided!')
        if not args.game:
            sys.exit(f'Error: argument "game" not provided!')
        if not args.gameabbr:
            sys.exit(f'Error: argument "gameabbr" not provided!')
    test_mode = not (args.test.lower().strip() == "no")
    # if a directory is specified, upload all images inside it
    if args.dir:
        for img in sorted(os.listdir(args.dir)):
            template = build_template(
                img,
                args.prefix,
                args.type,
                args.game,
                args.gameabbr,
                args.ani,
                args.credits,
            )
            if not test_mode:
                page = pywikibot.Page(site, f"File:{img}")
                if page.exists():
                    if page.text.startswith("#RINVIA") or page.text.startswith("#REDIRECT"):  # fmt: skip
                        page.delete("Bot: deleting redirect to upload actual image")
                    else:
                        print(f"Skipping {img} since it already exists and is not a redirect")  # fmt: skip
                        continue
                # os.system(f'python3 pwb.py upload -keep -noverify -ignorewarn -abortonwarn:exists "{os.path.join(args.dir, img)}" "{template}"')  # fmt: skip
                subprocess.run(
                    [
                        "python3",
                        "pwb.py",
                        "upload",
                        "-keep",
                        "-noverify",
                        "-ignorewarn",
                        "-abortonwarn:exists",
                        f"{os.path.join(args.dir, img)}",
                        f"{template}",
                    ]
                )
            else:
                print(f"{img}   >   {template}")
    # if a category is specified, update all its images
    elif args.cat:
        cat = pywikibot.Category(site, f"Categoria:{args.cat}")
        for page in pagegenerators.CategorizedPageGenerator(cat, recurse=True):
            img = page.title().replace("File:", "")
            template = build_template(
                img,
                args.prefix,
                args.type,
                args.game,
                args.gameabbr,
                args.ani,
                args.credits,
            )
            if not test_mode:
                page.text = template
                page.save("Bot: using new template for licenses and categories of Pokémon images")  # fmt: skip
            else:
                print(f"{img}   >   {template}")


# invoke main function
if __name__ == "__main__":
    main()
