import argparse, json, re, pywikibot

"""
This script updates Sprite template in Pokémon pages. This template should
display the following HOME models (each one both standard and shiny):
- Base form.
- Female model if different from male one.
- All alt forms if 5 or less; if more than 5 only base form is displayed.

Arguments:
--pokesfile: path of file with Pokémon data (already populated).
--formsfile: path of file with forms data (already populated).
--genderfile: path of file with gender data (already populated).
--updatepoke: ndexes of Pokémon to be updated, or "all" to update everything.
--summary: summary of edit (optional, already populated with a default message).
--test: "no" to perform actual modifications/uploads on website, otherwise only
a preview will be printed.
"""


# utility function that pads ndexes on 4 digits, keeping form abbr if any
def pad_ndexabbrs(ndexabbrs):
    # for each entry compute length of abbr (which is number of non-digits),
    # then use zfill to add leading zeros and obtain an ndex padded on 4 digits
    return [
        f"{ndexabbr.zfill(4 + len(re.sub(r"\d", "", ndexabbr)))}"
        for ndexabbr in ndexabbrs
    ]


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--pokesfile", default="data/wiki-util-data/poke-names.json")  # fmt: skip
    parser.add_argument("--formsfile", default="data/wiki-util-data/forms-availability.json")  # fmt: skip
    parser.add_argument("--genderfile", default="data/wiki-util-data/gender-data.json")  # fmt: skip
    parser.add_argument("--updatepoke", default="")
    parser.add_argument("--summary", default="Bot: updating Sprite template in Pokémon pages")  # fmt: skip
    parser.add_argument("--test", default="yes")
    args = parser.parse_args()
    # setup
    with open(args.pokesfile, "r") as file:
        pokes_data = json.load(file)
    with open(args.formsfile, "r") as file:
        forms_data = json.load(file)
    # for each entry compute length of abbr (which is number of non-digits),
    # then use zfill to add leading zeros and obtain an ndex padded on 4 digits
    forms = pad_ndexabbrs(forms_data)
    with open(args.genderfile, "r") as file:
        gender_data = json.load(file)
    site = pywikibot.Site()
    # check if all Pokémon need to be procedded or only specified ones
    if args.updatepoke == "all":
        pokes = [item["poke"] for item in pokes_data]
    else:
        pokes = pad_ndexabbrs(args.updatepoke.split(","))
    # process desired Pokémon pages
    for poke in pokes:
        poke_data = [item for item in pokes_data if item["poke"] == poke][0]
        poke_name = poke_data["it"]
        ndex = poke_data["ndex"]
        page = pywikibot.Page(site, poke_name)
        # ensure that Sprite template is included in page (even if disabled)
        if not re.search(r"\{\{[Ss]prite\b", page.text):
            print(f"Cannot update #{poke} {poke_name}: Sprite template not found")
            continue
        # get Pokémon data
        female_only = str(ndex) in gender_data["female-only"]
        gender_diff = str(ndex) in gender_data["gender-diffs"]
        gender_form = str(ndex) in gender_data["gender-forms"]
        # count Pokémon forms and ignore them if more than 5
        pokeabbrs = [form for form in forms if form.startswith(poke)]
        if len(pokeabbrs) > 5:
            pokeabbrs = []
        # remove first abbr if gender difference treated as useless form
        if gender_diff and len(pokeabbrs) > 0 and pokeabbrs[0] == f"{poke}F":
            pokeabbrs = pokeabbrs[1:]
        # find Sprite template in page
        index_start = [m for m in re.finditer(r"\{\{[Ss]prite\b", page.text)][0].start(0)  # fmt: skip
        index_end = page.text.index("}}", index_start)
        sprite_existing = page.text[index_start : (index_end + 2)]
        # build updated Sprite
        sprite_new = f"{{{{sprite|ndex={poke}"
        if gender_diff:
            sprite_new += "|bothgenders=yes"
        elif female_only:
            sprite_new += "|gender=f"
        for j in range(len(pokeabbrs)):
            pokeabbr = pokeabbrs[j]
            abbr = re.sub(r"\d", "", pokeabbr)
            sprite_new += f"|form{j + 1}={abbr}"
        sprite_new += "}}"
        # replace existing Sprite with with updated one
        if sprite_new != sprite_existing:
            if args.test.lower().strip() != "no":
                print(sprite_new)
            else:
                page.text = page.text.replace(sprite_existing, sprite_new)
                page.save(args.summary)


# invoke main function
if __name__ == "__main__":
    main()
