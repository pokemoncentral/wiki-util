import argparse, os, os.path, re
from scripts.userscripts.pkimgstools import import_data, get_poke_data, build_poke_page
'''
Quick infos about variables:
- 'poke' always represents number of Pokédex as string (without form abbr)
- 'pokeabbr' always represents number of Pokédex as string (with form abbr)
- 'ndex' always represents number of Pokédex as integer (without form abbr)
'''
# pwb pkimgs-create --pokepage all

parser = argparse.ArgumentParser()
parser.add_argument('--pokelistspath', default = 'data/pokelists/')
parser.add_argument('--pokepage', default = '')
parser.add_argument('--pokepagespath', default = 'data/pokepages-created/')
parser.add_argument('--pokeformspath', default = 'data/pokeforms/')
parser.add_argument('--exceptionspath', default = 'data/exceptions/')
parser.add_argument('--dexfile', default = 'data/utils/pokes_ndex.txt')
parser.add_argument('--genderdiffsfile', default = 'data/utils/genderdiffs.txt')
parser.add_argument('--genderformsfile', default = 'data/utils/genderforms.txt')
parser.add_argument('--femaleonlyfile', default = 'data/utils/femaleonly.txt')
parser.add_argument('--artsourcesfile', default = 'data/utils/artsources.txt')
parser.add_argument('--singlemsfile', default = 'data/utils/singleMS.txt')
parser.add_argument('--spscfile', default = 'data/utils/spsc.txt')
parser.add_argument('--rangerfile', default = 'data/utils/redirect_ranger.txt')
parser.add_argument('--goformsfile', default = 'data/utils/goforms.txt')
parser.add_argument('--defile', default = 'data/utils/pokes_de.txt')
parser.add_argument('--frfile', default = 'data/utils/pokes_fr.txt')
args = parser.parse_args()

if __name__ == '__main__':
    # import data
    getname, genderdiffs, genderforms, femaleonly, artsources, singlemsdata, spscdata, rangerdata, goforms = import_data(args.dexfile, args.genderdiffsfile, args.genderformsfile, args.femaleonlyfile, args.artsourcesfile, args.singlemsfile, args.spscfile, args.rangerfile, args.goformsfile)
    # create wikicode of subpage
    if args.pokepage:
        # import data for German and French names
        getdename = {}
        with open(args.defile, 'r') as file:
            for line in file:
                names = line.strip().split(',')
                getdename.update({names[1]: names[0]})
        getfrname = {}
        with open(args.frfile, 'r') as file:
            for line in file:
                names = line.strip().split(',')
                getfrname.update({names[1]: names[0]})
        # build page
        if not os.path.isdir(args.pokepagespath):
            os.mkdir(args.pokepagespath)
        if args.pokepage == 'all':
            lst = getname
        else:
            lst = args.pokepage.split(',')
        for poke in lst:
            gender, singleMS, spsc = get_poke_data(poke, genderdiffs, genderforms, femaleonly, singlemsdata, spscdata)
            # names
            name = getname[poke]
            dename = getdename[name]
            frname = getfrname[name]
            build_poke_page(poke, name, args.pokelistspath, args.pokepagespath, args.pokeformspath, artsources, goforms, args.exceptionspath, gender, singleMS, spsc, rangerdata, dename, frname)
