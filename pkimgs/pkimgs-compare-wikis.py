import argparse, os, json, re
import pywikibot
from pywikibot import pagegenerators


# get a list with all images in specified site and category
def get_imgs(fam, lang, cat_name):
    site = pywikibot.Site(lang, fam=fam)
    cat = pywikibot.Category(site, cat_name)
    pages = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
    imgs = [page.title() for page in pages]
    return imgs


# compare number of images in source and destination
def compare_pokeimgs(poke, pokeimgs_source, pokeimgs_dest, discrepancies):
    num_source = len(pokeimgs_source)
    num_dest = len(pokeimgs_dest)
    if num_source != num_dest:
        discrepancies += pokeimgs_source
        print(f"#{poke}: source {num_source}, dest {num_dest}")
        print("\n".join(pokeimgs_source + ["------------"] + pokeimgs_dest))
        print("")
    return discrepancies


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--catsfile", default="data/pokepages-utils/categories-names.json")  # fmt: skip
    parser.add_argument("--game", default="")
    parser.add_argument("--sourcefam", default="archibulba")
    parser.add_argument("--destfam", default="encypok")
    parser.add_argument("--sourcelang", default="en")
    parser.add_argument("--destlang", default="it")
    parser.add_argument("--outdir", default="data")
    args = parser.parse_args()
    # read file with categories data and get their names
    with open(args.catsfile, "r") as file:
        cats_data = json.load(file)
    cat_name_source = cats_data[args.game][args.sourcelang]
    cat_name_dest = cats_data[args.game][args.destlang]
    print(f'Comparing game "{args.game}" - source "{cat_name_source}" ({args.sourcelang}), destination "{cat_name_dest}" ({args.destlang})')  # fmt: skip
    # list images in source and destination category
    imgs_source = get_imgs(args.sourcefam, args.sourcelang, cat_name_source)
    imgs_dest = get_imgs(args.destfam, args.destlang, cat_name_dest)
    # print total number of images in source and destination
    print(f"Total: source {len(imgs_source)}, dest {len(imgs_dest)}")
    # find images without ndex (lookahead/lookbehind not neeeded because
    # name space and file extension are included)
    other_source = [i for i in imgs_source if not re.search(r"\D\d{4}\D", i)]
    other_dest = [i for i in imgs_dest if not re.search(r"\D\d{4}\D", i)]
    # find max ndex
    nums_source = [i for i in imgs_source if not i in other_source]
    nums_dest = [i for i in imgs_dest if not i in other_dest]
    last_ndex = max([int(re.match(r".*(\d{4}).*", i).group(1)) for i in nums_source + nums_dest])  # fmt: skip
    print(f"Checking all ndexes from #0000 to #{str(last_ndex).zfill(4)}\n")
    # initialize list with source images that may be missing from destination
    discrepancies = []
    # compare by counting number of images for each ndex
    for ndex in range(1, last_ndex + 1):
        poke = str(ndex).zfill(4)
        pokeimgs_source = [i for i in imgs_source if re.search(r"\D{}\D".format(poke), i)]  # fmt: skip
        pokeimgs_dest = [i for i in imgs_dest if re.search(r"\D{}\D".format(poke), i)]
        discrepancies = compare_pokeimgs(poke, pokeimgs_source, pokeimgs_dest, discrepancies)  # fmt: skip
    # compare number of images without ndex
    discrepancies = compare_pokeimgs("____", other_source, other_dest, discrepancies)
    # check if a file was specified to list all discrepancies
    if not args.outdir:
        print(f"Found {len(discrepancies)} discrepancies")
    else:
        output_file_path = os.path.join(args.outdir, f"imgs-discrepancies-{args.game}.txt")  # fmt: skip
        print(f"Writing {len(discrepancies)} discrepancies to file {output_file_path}")
        with open(output_file_path, "w") as file:
            file.write("\n".join(discrepancies) + "\n")


# invoke main function
if __name__ == "__main__":
    main()
