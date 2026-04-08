import pywikibot, argparse, re, os, os.path, sys, subprocess, json, importlib
from pywikibot import pagegenerators

"""
This script fills "Pokeartwork" template fields: it can be used to mass upload images
in a directory or to update an entire category on Pokémon Central Wiki. Arguments:
--dir: directory with images to upload.
--cat: category with images to update (without "Categoria:").
--file: file with images to update.
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
    # initialize some variables used in this function
    template = None
    source = None
    skip = False
    shiny = "no"
    altform = "no"
    # remove extension and, if present, final number
    file_name = re.sub(r"\.\w+$", r"", file_name)
    file_name = re.sub(r" \d{1,2}$", r"", file_name)
    # find artwork source; they are sorted from longest to shortest to avoid
    # problems with sources such as "promo HOME SV" that would be classified as
    # "SV" without sorting
    for entry in sorted(artsources, key=len, reverse=True):
        if file_name.endswith(f" {entry}"):
            source = entry
            source_param = artsources[entry]["pokeartwork_param"]
            source_cat = artsources[entry]["cat"]
            break
    if source:
        # remove source
        file_name = re.sub(f" {source}$", r"", file_name)
        # check if shiny
        if file_name.endswith(" cromatico"):
            shiny = "yes"
            file_name = re.sub(r" cromatico$", r"", file_name)
        # check if ndex or name
        if re.search(r"^Artwork\d", file_name):
            ndex = re.sub(r"Artwork(\w+)( tutte le forme)?", r"\1", file_name)
            name = ""
            # if ndex doesn't follow standard, reset it to avoid building a wrong template
            if not re.search(r"^\d{4}\w{0,4}$", ndex):
                ndex = ""
            elif re.search(r"\D", ndex) or file_name.endswith(" tutte le forme"):
                altform = "yes"
        else:
            ndex = ""
            name = re.sub(r"^Artwork ", r"", file_name)
        # fix/skip special cases
        if source == "Corp":
            if ndex:
                # fix Corp parameter to insert gen instead of "Corp"
                gen = ndex_to_gen[re.sub(r"\D", r"", ndex)]
                source_cat = (f"{{{{subst:#invoke: GenerationsData | getOrdinal | {gen} }}}}")  # fmt: skip
            else:
                # skip Corp artworks without ndex, better manage them manually
                skip = True
        elif source.startswith("anime "):
            source_cat = source_cat.replace("anime ", "")
        # check if current image was identified correctly
        if skip or (not ndex and not name):
            template = None
        else:
            template = "|".join(
                [
                    "{{pokeartwork",
                    f"ndex={ndex}",
                    f"name={name}",
                    f"shiny={shiny}",
                    f"altform={altform}",
                    f"{source_param}={source_cat}",
                    f"credits={credits}}}}}",
                ]
            )
            # remove empty fields before returning final string
            template = re.sub(r"\|\w+=(?=[\|\}])", r"", template)
    return template


# process existing file: build template and overwrite it if different
def process_wiki_file(file_page, test_mode=True):
    # check that specified file page exists
    if not page.exists():
        print(f"File not found in wiki: {file_page.title()}")
        return
    # skip files with other naming
    if not file_page.title(with_ns=False).startswith("Artwork"):
        print(f"Unprocessable file: {file_page.title()}")
        return
    img = file_page.title().replace("File:", "")
    template = build_template(img, artsources, ndex_to_gen, args.credits)
    # check if template was built correctly
    if not template:
        print(f"Failed to build template: {img}")
        return
    if test_mode:
        print(f"{img}   >   {template}")
    else:
        if file_page.text.strip() == template.strip():
            print(f"Skipping page {file_page.title()}")
        else:
            file_page.text = template
            file_page.save("Bot: using new template for licenses and categories of Pokémon images")  # fmt: skip


# main function
if __name__ == "__main__":
    site = pywikibot.Site()
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="")
    parser.add_argument("--cat", default="")
    parser.add_argument("--file", default="")
    parser.add_argument("--credits", default="")
    parser.add_argument("--artsourcesfile", default="data/pokepages-utils/artsources.json")  # fmt: skip
    parser.add_argument("--test", default="yes")
    args = parser.parse_args()
    # check arguments
    if args.dir and not os.path.isdir(args.dir):
        sys.exit(f'Error: directory "{args.dir}" not found!')
    test_mode = not (args.test.lower().strip() == "no")
    # get sources data
    with open(args.artsourcesfile, "r") as file:
        artsources = json.load(file)
    ndex_to_gen = utils.get_ndex_gen_dict()
    # if a directory is specified, upload all images inside it
    if args.dir:
        for img in sorted(os.listdir(args.dir)):
            template = build_template(img, artsources, ndex_to_gen, args.credits)
            if not template:
                print(f"Cannot build template for file, skipping upload: {img}")
                continue
            if test_mode:
                print(f"{img}   >   {template}")
            else:
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
                        f'"{os.path.join(args.dir, img)}"',
                        f'"{template}"',
                    ]
                )
    # if a category is specified, process images in it (recursively)
    elif args.cat:
        cat = pywikibot.Category(site, f"Categoria:{args.cat}")
        for page in pagegenerators.CategorizedPageGenerator(cat, recurse=True):
            process_wiki_file(page, test_mode)
    # if a local file is specified, read titles from it and process them on wiki
    elif args.file:
        if not os.path.isfile(args.file):
            sys.exit(f"Cannot find specified file: {args.file}")
        with open(args.file, "r") as file:
            titles = [t for t in file.read().splitlines() if t]
        for title in titles:
            page = pywikibot.Page(site, f"File:{title}")
            process_wiki_file(page, test_mode)
