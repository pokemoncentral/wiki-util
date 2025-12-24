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
    parser.add_argument("--genderdiffsfile", default="data/pokepages-utils/genderdiffs.txt")
    parser.add_argument("--genderformsfile", default="data/pokepages-utils/genderforms.txt"  )
    parser.add_argument("--femaleonlyfile", default="data/pokepages-utils/femaleonly.txt")
    parser.add_argument("--artsourcesfile", default="data/pokepages-utils/artsources.txt")
    parser.add_argument("--singlemsfile", default="data/pokepages-utils/singleMS.txt")
    parser.add_argument("--availdir", default="data/pokepages-availability")
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
            availdata,
            rangerdata,
            goforms,
        ) = import_data(
            args.genderdiffsfile,
            args.genderformsfile,
            args.femaleonlyfile,
            args.artsourcesfile,
            args.singlemsfile,
            args.availdir,
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
                availdata,
                rangerdata,
                getenname[itname],
                getesname[itname],
                getdename[itname],
                getfrname[itname],
            )


# invoke main function
if __name__ == "__main__":
    main()
