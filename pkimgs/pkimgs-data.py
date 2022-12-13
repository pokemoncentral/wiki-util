import pywikibot, argparse, os, os.path, re
from scripts.userscripts.pkimgstools import import_ndex
from pywikibot import pagegenerators
'''
Quick infos about variables:
- 'poke' always represents number of Pokédex as string (without form abbr)
- 'pokeabbr' always represents number of Pokédex as string (with form abbr)
- 'ndex' always represents number of Pokédex as integer (without form abbr)
'''
# pwb pkimgs-data --catlist all --pokelist all --pokerank all --download all

# get list of images in given category and save it to text file
def build_cat_list(site, cat, catspath):
    pages = pagegenerators.CategorizedPageGenerator(pywikibot.Category(site, f'Categoria:{cat}'))
    with open(f'{os.path.join(catspath, cat.replace(":", ";"))}.txt', 'w') as file:
        file.write('\n'.join([page.title() for page in pages]).replace('File:', '') + '\n')

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
    # imgs is the union of all lists, imgs_distinct the final list without duplicates
    imgs = []
    imgs_distinct = []
    for cat in os.listdir(catspath):
        imgs += get_poke_in_cat(poke, name, cat, catspath)
    for img in imgs:
        if img not in imgs_distinct:
            imgs_distinct.append(img)
    with open(f'{os.path.join(pokelistspath, poke)}.txt', 'w') as file:
        file.write('\n'.join(imgs_distinct) + '\n')

# get number of images for given Pokémon
def get_poke_rank(poke, pokespath):
    with open('{}.txt'.format(os.path.join(pokespath, poke)), 'r') as file:
        lines = file.read().splitlines()
    return len(lines)

# download wikicode of pokepage from wiki and save it to text file
def download_pokepage(site, poke, name, downloadspath):
    destfile = os.path.join(downloadspath, '{}.txt'.format(poke))
    page = pywikibot.Page(site, '{}/Immagini'.format(name))
    with open(destfile, 'w') as file:
        file.write(page.text.strip() + '\n')

parser = argparse.ArgumentParser()
parser.add_argument('--catlist', default = '')
parser.add_argument('--catlistspath', default = 'data/pokepages-catlists/')
parser.add_argument('--pokelist', default = '')
parser.add_argument('--pokelistspath', default = 'data/pokepages-pokelists/')
parser.add_argument('--pokerank', default = '')
parser.add_argument('--pokerankfile', default = 'data/ranking.txt')
parser.add_argument('--catsfile', default = 'data/pokepages-utils/cats.txt')
parser.add_argument('--dexfile', default = 'data/pokepages-utils/pokes_names.csv')
parser.add_argument('--download', default = '')
parser.add_argument('--downloadspath', default = 'data/pokepages-downloaded/')
args = parser.parse_args()

if __name__ == '__main__':
    # import data
    site = pywikibot.Site()
    getname, getenname, getesname, getdename, getfrname = import_ndex(args.dexfile)
    # update categories
    if args.catlist:
        if not os.path.isdir(args.catlistspath):
            os.mkdir(args.catlistspath)
        if args.catlist == 'all':
            with open(args.catsfile, 'r') as file:
                allcats = file.read().splitlines()
            for cat in allcats:
                build_cat_list(site, cat, args.catlistspath)
                print(f'Retrieved list of images in category "{cat}"')
        else:
            build_cat_list(site, args.catlist, args.catlistspath)
            print(f'Retrieved list of images in category "{args.catlist}"')
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
        print(f'Updated {args.pokelistspath}')
    # count number of images for given Pokémon or for all Pokémon
    if args.pokerank:
        print('')
        if args.pokerank == 'all':
            pokerank_print = ''
            ranks = {}
            for poke in getname:
                ranks.update({poke: get_poke_rank(poke, args.pokelistspath)})
            ranking = sorted(ranks.items(), key = lambda x: x[1], reverse = True)
            pokerank_print += f'Total: {sum([n[1] for n in ranking])}\n\n'
            for item in ranking:
                poke, rank = item
                name = getname[poke]
                # Pokémon name/nickname cannot be longer than 12 characters
                pokerank_print += f'{poke} {name.ljust(12, " ")}   {rank}\n'
        else:
            pokerank_print = get_poke_rank(args.pokerank, args.pokelistspath)
        print('\n'.join(pokerank_print.splitlines()[:12]))
        with open(args.pokerankfile, 'w') as file:
            file.write(pokerank_print)
    # download subpages from wiki
    if args.download:
        if args.download == 'all':
            lst = getname
        else:
            lst = args.download.split(',')
        if not os.path.isdir(args.downloadspath):
            os.mkdir(args.downloadspath)
        # retrieve subpages
        for poke in lst:
            download_pokepage(site, poke, getname[poke], args.downloadspath)
