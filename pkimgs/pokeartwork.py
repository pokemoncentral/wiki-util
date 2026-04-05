import pywikibot, argparse, re, os, os.path, sys, subprocess, json, importlib
from pywikibot import pagegenerators

"""
This script fills "Pokeartwork" template fields: it can be used to mass upload images
in a directory or to update an entire category on Pokémon Central Wiki. Arguments:
--dir: directory with images to upload.
--cat: category with images to update (without "Categoria:").
--credits: credits for images (wikicode, optional).
--artsourcesfile: path of file with sources data (already populated).
--test: "no" to perform actual modifications/uploads on website, otherwise only a preview will be printed.

Artwork names for single Pokémon are built as follows:
- "Artwork" prefix.
- Number of Pokédex, with leading zeros and form abbreviation if applicable, immediately
after prefix (i.e. they are not separated by a space).
- If Pokémomn is shiny, "cromatico" is added.
- If displayed Pokémon are all forms of same species, "tutte le forme" is added.
- Source, as name or abbreviation (see keys in pkimgs/pokepages-utils/artsources.json).
- If multiple artwork of same Pokémon from same source are available, a number is
appended before file extension.
Here are some examples:
Artwork0181 HGSS.png
Artwork0905 anime OP 2.png
Artwork0585I NB.png
Artwork0384M cromatico anime XY 2.png
Artwork0648 tutte le forme N2B2.png

If an artwork contains multiple Pokémon, number of Pokédex should be replaced by:
- If displayed Pokémon form a group with a name (e.g.a legendary duo/trio), its name.
- Otherwise, name of single Pokémon without form name and sorted by ndex.
Examples:
Artwork Trio Drago Pt.png
Artwork Reshiram Zekrom distribuzione 2018.png
Artwork Ampharos Treecko Lilligant PF.png
"""

# import utils from 'shared' directory of this repository
script_path = os.path.realpath(__file__)
script_dir = os.path.dirname(script_path)
utils_dir = os.path.join(os.path.dirname(script_dir), "shared")
spec = importlib.util.spec_from_file_location("utils", os.path.join(utils_dir, "utils.py"))  # fmt: skip
utils = importlib.util.module_from_spec(spec)
sys.modules["utils"] = utils
spec.loader.exec_module(utils)


def build_template(file_name, artsources, ndex_to_gen, credits=""):
    # remove extension and, if present, final number
    file_name = re.sub(r"\.\w+$", r"", file_name)
    file_name = re.sub(r" \d{1,2}$", r"", file_name)
    # find artwork source
    source = None
    # sorted from longest to shortest to avoid problems with sources such as
    # "promo HOME SV" that would be classified as SV" without sorting
    for entry in sorted(artsources, key=len, reverse=True):
        if file_name.endswith(f" {entry}"):
            source = entry
            source_param = artsources[entry]["pokeartwork_param"]
            source_cat = artsources[entry]["cat"]
            break
    if not source:
        template = None
    else:
        # remove source
        file_name = re.sub(f" {source}$", r"", file_name)
        # check if shiny
        if file_name.endswith(" cromatico"):
            shiny = "yes"
            file_name = re.sub(r" cromatico$", r"", file_name)
        else:
            shiny = "no"
        # check if ndex or name
        if re.search(r"^Artwork\d", file_name):
            ndex = re.sub(r"Artwork(\w+)( tutte le forme)?", r"\1", file_name)
            name = ""
            if re.search(r"\D", ndex) or file_name.endswith(" tutte le forme"):
                altform = "yes"
            else:
                altform = "no"
        else:
            ndex = ""
            name = re.sub(r"^Artwork ", r"", file_name)
            altform = "no"
        # fix/skip special cases
        skip = False
        if source == "Corp":
            if ndex:
                # fix Corp parameter to insert gen instead of "Corp"
                gen = ndex_to_gen[re.sub(r"\D", r"", ndex)]
                source_cat = f"{{{{subst:#invoke: GenerationsData | getOrdinal | {gen} }}}}"
            else:
                # skip Corp artworks without ndex, better manage them manually
                skip = True
        if skip:
            template = None
        else:
            template = f"{{{{pokeartwork|ndex={ndex}|name={name}|shiny={shiny}|altform={altform}|{source_param}={source_cat}|credits={credits}}}}}"
            # remove empty fields before returning final string
            template = re.sub(r"\|\w+=(?=[\|\}])", r"", template)
    return template


# main function
if __name__ == "__main__":
    site = pywikibot.Site()
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="")
    parser.add_argument("--cat", default="")
    parser.add_argument("--credits", default="")
    parser.add_argument("--artsourcesfile", default="data/pokepages-utils/artsources.json")  # fmt: skip
    parser.add_argument("--test", default="yes")
    args = parser.parse_args()
    # check arguments
    if args.dir and not os.path.isdir(args.dir):
        sys.exit(f'Error: directory "{args.dir}" not found!')
    # get sources data
    with open(args.artsourcesfile, "r") as file:
        artsources = json.load(file)
    ndex_to_gen = utils.get_ndex_gen_dict()
    # if a directory is specified, upload all images inside it
    if args.dir:
        for img in sorted(os.listdir(args.dir)):
            template = build_template(img, artsources, ndex_to_gen, args.credits)
            if args.test.lower().strip() == "no":
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
                        '"{os.path.join(args.dir, img)}"',
                        f'"{template}"',
                    ]
                )
            else:
                print(f"{img}   >   {template}")
    # process images in specified category
    elif args.cat:
        cat = pywikibot.Category(site, f"Categoria:{args.cat}")
        for page in pagegenerators.CategorizedPageGenerator(cat, recurse=True):
            if not page.title(with_ns=False).startswith("Artwork"):
                print(f"Unprocessable file: {page.title()}")
                continue
            img = page.title().replace("File:", "")
            template = build_template(img, artsources, ndex_to_gen, args.credits)
            if not template:
                print(f"Failed to build template: {img}")
                continue
            if args.test.lower().strip() == "no":
                if page.text.strip() == template.strip():
                    print(f"Skipping page {page.title()}")
                else:
                    page.text = template
                    page.save("Bot: using new template for licenses and categories of Pokémon images")  # fmt: skip
            else:
                print(f"{img}   >   {template}")
