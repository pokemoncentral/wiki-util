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
parser.add_argument('--dexfile', default = 'data/pokepages-utils/pokes_ndex.txt')
parser.add_argument('--genderdiffsfile', default = 'data/pokepages-utils/genderdiffs.txt')
parser.add_argument('--genderformsfile', default = 'data/pokepages-utils/genderforms.txt')
parser.add_argument('--femaleonlyfile', default = 'data/pokepages-utils/femaleonly.txt')
parser.add_argument('--artsourcesfile', default = 'data/pokepages-utils/artsources.txt')
parser.add_argument('--singlemsfile', default = 'data/pokepages-utils/singleMS.txt')
parser.add_argument('--availdir', default = 'data/pokepages-availability')
parser.add_argument('--rangerfile', default = 'data/pokepages-utils/redirect_ranger.txt')
parser.add_argument('--goformsfile', default = 'data/pokepages-utils/goforms.txt')
parser.add_argument('--defile', default = 'data/pokepages-utils/pokes_de.txt')
parser.add_argument('--frfile', default = 'data/pokepages-utils/pokes_fr.txt')
args = parser.parse_args()

if __name__ == '__main__':
    # import data
    getname, genderdiffs, genderforms, femaleonly, artsources, singlemsdata, availdata, rangerdata, goforms = import_data(args.dexfile, args.genderdiffsfile, args.genderformsfile, args.femaleonlyfile, args.artsourcesfile, args.singlemsfile, args.availdir, args.rangerfile, args.goformsfile)
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
            gender, singleMS, avail = get_poke_data(poke, genderdiffs, genderforms, femaleonly, singlemsdata, availdata)
            # names
            name = getname[poke]
            dename = getdename[name]
            frname = getfrname[name]
            build_poke_page(poke, name, args.pokelistspath, args.pokepagespath, args.pokeformspath, artsources, goforms, args.exceptionspath, gender, singleMS, avail, rangerdata, dename, frname)
