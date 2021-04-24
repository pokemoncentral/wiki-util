import pywikibot, argparse, os, os.path, re
from scripts.userscripts.pkimgstools import import_ndex
'''
Quick infos about variables:
- 'poke' always represents number of Pokédex as string (without form abbr)
- 'pokeabbr' always represents number of Pokédex as string (with form abbr)
- 'ndex' always represents number of Pokédex as integer (without form abbr)
'''
# pwb pkimgs-data --catlist all --pokelist all --pokerank all --download all > data/ranking.txt

# get list of images in given category and save it to text file
def build_cat_list(cat, catspath):
    os.system('python3 pwb.py listpages -format:3 -cat:"{}" > "{}.txt"'.format(cat, os.path.join(catspath, cat.replace(':', ';'))))

# get list of images in given category with given Pokémon
def get_poke_in_cat(poke, name, cat, catspath):
    # search ndex or name
    # do note that Stadium 2 models are Sprstad2<ndex>, so \D{}\D won't find them
    regex = r'({}\D|\b{}\b)'.format(poke, name)
    with open(os.path.join(catspath, cat.replace(':', ';')), 'r') as catfile:
        lines = catfile.read().splitlines()
    lst = []
    for line in lines:
        if re.search(regex, line) and line not in lst:
            lst.append(line)
    return lst

# get list of images for given Pokémon and save it to text file
def build_poke_list(poke, name, catspath, pokelistspath):
    # create dest file if not exists, otherwise delete its content
    destfile = '{}.txt'.format(os.path.join(pokelistspath, poke))
    if not os.path.isfile(destfile):
        with open(destfile, 'w') as file:
            pass
    else:
        open(destfile, 'w').close()
    # imgs is the union of all lists, imgsU the final list without duplicates
    imgs = []
    imgsU = []
    for cat in os.listdir(catspath):
        imgs += get_poke_in_cat(poke, name, cat, catspath)
    with open(destfile, 'a') as file:
        for img in imgs:
            if img not in imgsU:
                imgsU.append(img)
                file.write(img + '\n')

# get number of images for given Pokémon
def get_poke_rank(poke, pokespath):
    with open('{}.txt'.format(os.path.join(pokespath, poke)), 'r') as file:
        lines = file.read().splitlines()
    return len(lines)

# download wikicode of pokepage from wiki and save it to text file
def download_pokepage(poke, name, downloadspath):
    site = pywikibot.Site()
    destfile = os.path.join(downloadspath, '{}.txt'.format(poke))
    page = pywikibot.Page(site, '{}/Immagini'.format(name))
    with open(destfile, 'w') as file:
        file.write(page.text.strip() + '\n')

parser = argparse.ArgumentParser()
parser.add_argument('--catlist', default = '')
parser.add_argument('--catlistspath', default = 'data/catlists/')
parser.add_argument('--pokelist', default = '')
parser.add_argument('--pokelistspath', default = 'data/pokelists/')
parser.add_argument('--pokerank', default = '')
parser.add_argument('--catsfile', default = 'data/utils/cats.txt')
parser.add_argument('--dexfile', default = 'data/utils/pokes_ndex.txt')
parser.add_argument('--download', default = '')
parser.add_argument('--downloadspath', default = 'data/pokepages-downloaded/')
args = parser.parse_args()

if __name__ == '__main__':
    # import data
    getname = import_ndex(args.dexfile)
    # update categories
    if args.catlist:
        if not os.path.isdir(args.catlistspath):
            os.mkdir(args.catlistspath)
        if args.catlist == 'all':
            with open(args.catsfile, 'r') as file:
                allcats = file.read().splitlines()
            for cat in allcats:
                build_cat_list(cat, args.catlistspath)
        else:
            build_cat_list(args.catlist, args.catlistspath)
    # update lists of images
    if args.pokelist:
        if not os.path.isdir(args.pokelistspath):
            os.mkdir(args.pokelistspath)
        if args.pokelist == 'all':
            lst = getname
        else:
            lst = args.pokelist.split(',')
        for poke in lst:
            build_poke_list(poke, getname[poke], args.catlistspath, args.pokelistspath)
    # count number of images for given Pokémon or for all Pokémon
    if args.pokerank:
        if args.pokerank == 'all':
            ranks = {}
            for poke in getname:
                ranks.update({poke: get_poke_rank(poke, args.pokelistspath)})
            ranking = sorted(ranks.items(), key = lambda x: x[1], reverse = True)
            print('Total: {}\n'.format(sum([n[1] for n in ranking])))
            for item in ranking:
                poke, rank = item
                name = getname[poke]
                print('{} {}{}   {}'.format(poke, name, ' ' * (12 - len(name)), rank))
        else:
            print(get_poke_rank(args.pokerank, args.pokelistspath))
    # download subpages from wiki
    if args.download:
        if args.download == 'all':
            lst = getname
        else:
            lst = args.download.split(',')
        if not os.path.isdir(args.downloadspath):
            os.mkdir(args.downloadspath)
        # retrieve subpages
        site = pywikibot.Site()
        for poke in lst:
            download_pokepage(poke, getname[poke], args.downloadspath)
