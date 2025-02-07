import pywikibot, argparse, re, os, os.path, sys
from pywikibot import pagegenerators

"""
This script fills "Sprello" template fields: it can be used to mass upload images
in a directory or to update an entire category on Pokémon Central Wiki. Arguments:
--dir: directory with images to upload.
--cat: category with images to update (without "Categoria:").
--prefix: if uploading/updating main series images (excluding mini sprites), can
be "Spr" for sprite/models or "Icon" for mugshots.
--type: if uploading/updating main series images, can be "sprite", "modelli", "mini sprite".
--game: if uploading/updating main series images, specify game/generation.
--gameabbr: if uploading/updating main series images (excluding mini sprites), specify abbreviation of game.
--ani: if uploading/updating main series images (excluding mini sprites), can be "yes" or "no".
--credits: credits for images (wikicode, optional).
--test: "no" to perform actual modifications/uploads on website, otherwise only a preview will be printed.

In all file names mentioned in following comments it holds that:
- <...> indicates something variable, for example <ndex> is National Pokédex number.
- [...] indicates something that may be present or not.
- | indicates alternative among two or more options.
"""


# fmt: off
"""
Build template for sprites, models and icons in main series games (NOT mini sprites).
File name is "[Spr|Icon]<game>[m|f][d][sh]<ndex>.<ext>", where:
- [Spr|Icon] is 'Spr' for sprites and models, 'Icon' for mugshots.
- <game> is abbr of game(s), for example 'nb' is for "Pokémon Nero e Bianco".
- [m|f] is 'f' if female and 'm' in any other case, it is not used before generation 4.
- [d] is used for back sprites/models.
- [sh] is used for shiny sprites/models.
- <ndex> is National Pokédex number, including abbr of form if applicable.
- <ext> is file extension.
"""  # fmt: on
def build_main_template(img, prefix, type, game, gameabbr, ani, credits):
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
    return f"{{{{sprello|type={type}|ndex={ndex}|game={game}|ani={ani}|back={back}|shiny={shiny}|female={female}|altform={altform}|credits={credits}}}}}"


# fmt: off
"""
Build template for main series mini sprites. File name is
"[Ani]<ndex>MS<gen|game>[OW*[sh]].<ext>", where:
- [Ani] is used for animated mini sprites.
- <ndex> works as above, except generation 1/2 where is name of a Pokémon (many
of them shared same mini sprite).
- <gen|game> is last generation or game where it is used.
- [OW*[sh]] is only used for partner Pokémon in HGSS.
- <ext> is file extension, png for static mini sprites and gif for animated ones.

AniClefairyMS1.gif
AniClefairyMS2.gif
001MS4OWEsh.gif
Ani001MS5.gif
001MS5.png
001MS7.png
001MS.png
001MSDLPS.png
"""  # fmt: on
def build_main_ms_template(img, game, credits):
    ndex = re.sub(r"^(Ani)?(.+?)MS.+$", r"\2", img)
    if re.search(r"^[A-z]", ndex):
        ndex = "000"
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
    return f"{{{{sprello|type=mini sprite|ndex={ndex}|game={game}|ani={ani}|shiny={shiny}|altform={altform}|credits={credits}}}}}"


# fmt: off
"""
Build template for HOME models (both standard and resized). File name is
"Home[m|f][sh]<ndex>[ r].png" for standard models and Mini[m|f][sh]<ndex>[ r].png
for resized models, where:
- [m|f] works as above.
- [sh] works as above.
- <ndex> works as above.
- [ r] is used for back models.
"""  # fmt: on
def build_home_template(img, credits=""):
    if img.startswith("Home"):
        type = "modelli"
        ani = "no"
        if " r" in img or "_r" in img:
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
    return f"{{{{sprello|type={type}|ndex={ndex}|game=Pokémon HOME|ani={ani}|back={back}|shiny={shiny}|female={female}|altform={altform}|credits={credits}}}}}"


# fmt: off
"""
Build template for GO models. File name is "GO<ndex>[ <event>][ f][ s].png", where:
- <ndex> works as above.
- <event> is special event, for example "FashionWeek21" or "Clone".
- [ f] is used for female models.
- [ s] is used for shiny models.
"""  # fmt: on
def build_go_template(img):
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
    return f"{{{{sprello|type=modelli|ndex={ndex}|game=Pokémon GO|shiny={shiny}|female={female}|altform={altform}|event={event}}}}}"


# build appropriate template
def build_template(img, prefix, type, game, gameabbr, ani, credits):
    if prefix in ["Spr", "Icon"]:
        template = build_main_template(img, prefix, type, game, gameabbr, ani, credits)
    elif type == "mini sprite":
        template = build_main_ms_template(img, game, credits)
    elif re.search(r"^(Home|Mini)[mf]", img):
        template = build_home_template(img, credits=credits)
    elif img.startswith("GO"):
        template = build_go_template(img)
    return re.sub(r"\|\w+=(?=[\|\}])", r"", template)  # remove empty fields


# main function
if __name__ == "__main__":
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
            if args.test.lower().strip() == "no":
                page = pywikibot.Page(site, f"File:{img}")
                if page.exists():
                    if page.text.startswith("#RINVIA") or page.text.startswith("#REDIRECT"):  # fmt: skip
                        page.delete("Bot: deleting redirect to upload actual image")
                    else:
                        print(f"Skipping {img} since it already exists and is not a redirect")  # fmt: skip
                        continue
                os.system(f'python3 pwb.py upload -keep -noverify -ignorewarn -abortonwarn:exists "{os.path.join(args.dir, img)}" "{template}"')  # fmt: skip
            else:
                print(f"{img}   >   {template}")
    # if a category is specified, update all its images
    elif args.cat:
        cat = pywikibot.Category(site, f"Categoria:{args.cat}")
        for page in pagegenerators.CategorizedPageGenerator(cat):
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
            if args.test.tolower().strip() == "no":
                page.text = template
                page.save("Bot: using new template for licenses and categories of Pokémon images")  # fmt: skip
            else:
                print(f"{img}   >   {template}")

# f"{{{{sprello|type={type}|ndex={ndex}|game={game}|ani={ani}|back={back}|shiny={shiny}|female={female}|altform={altform}|credits={credits}}}}}"
