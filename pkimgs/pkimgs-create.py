import argparse, os, os.path, re
from scripts.userscripts.pkimgstools import (
    import_ndex,
    import_data,
    get_poke_data,
    build_poke_page,
)

"""
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


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    # fmt: off
    parser.add_argument("--pokelistspath", default="data/pokepages-pokelists/")
    parser.add_argument("--pokepage", default="")
    parser.add_argument("--pokepagespath", default="data/pokepages-created/")
    parser.add_argument("--pokeformspath", default="data/pokepages-pokeforms/")
    parser.add_argument("--exceptionspath", default="data/pokepages-exceptions/")
    parser.add_argument("--dexfile", default="data/wiki-util-data/poke-names.json")
    parser.add_argument("--genderdatafile", default="data/wiki-util-data/gender-data.json")
    parser.add_argument("--artsourcesfile", default="data/pokepages-utils/artsources.json")
    parser.add_argument("--singlemsfile", default="data/pokepages-utils/singleMS.txt")
    parser.add_argument("--availpokesfile", default="data/wiki-util-data/poke-availability.json")
    parser.add_argument("--availformsfile", default="data/wiki-util-data/forms-availability.json")
    parser.add_argument("--rangerfile", default="data/pokepages-utils/redirect_ranger.txt")
    parser.add_argument("--goformsfile", default="data/pokepages-utils/goforms.txt")
    # fmt: on
    args = parser.parse_args()
    # create wikicode of subpage
    if args.pokepage:
        # import data
        getname, getenname, getesname, getdename, getfrname = import_ndex(args.dexfile)
        (
            genderdiffs,
            genderforms,
            femaleonly,
            artsources,
            singlemsdata,
            availpokes,
            availforms,
            rangerdata,
            goforms,
        ) = import_data(
            args.genderdatafile,
            args.artsourcesfile,
            args.singlemsfile,
            args.availpokesfile,
            args.availformsfile,
            args.rangerfile,
            args.goformsfile,
        )
        # build page
        if not os.path.isdir(args.pokepagespath):
            os.mkdir(args.pokepagespath)
        if args.pokepage == "all":
            lst = getname
        else:
            lst = args.pokepage.split(",")
        for poke in lst:
            itname = getname[poke]
            gender, singleMS = get_poke_data(
                poke, genderdiffs, genderforms, femaleonly, singlemsdata
            )
            build_poke_page(
                poke,
                itname,
                args.pokelistspath,
                args.pokepagespath,
                args.pokeformspath,
                artsources,
                goforms,
                args.exceptionspath,
                gender,
                singleMS,
                availpokes,
                availforms,
                rangerdata,
                getenname[itname],
                getesname[itname],
                getdename[itname],
                getfrname[itname],
            )


# invoke main function
if __name__ == "__main__":
    main()
