import pywikibot, argparse, os.path, re
from scripts.userscripts.pkimgstools import import_data, get_poke_data, get_forms, get_spinoff_imgs, build_arts, build_main, build_spinoffs
'''
Quick infos about variables:
- 'poke' always represents number of Pokédex as string (without form abbr)
- 'pokeabbr' always represents number of Pokédex as string (with form abbr)
- 'ndex' always represents number of Pokédex as integer (without form abbr)
'''
# pwb pkimgs-update --updatepoke all

# get text for given section (artworks, main series or spin-offs)
def get_section_text(pagetext, section):
    delimiters = {
    'artwork': ['==Artwork==\n{{pokemonimages/head|content=\n', '}}\n\n==Sprite e modelli=='],
    'main': ['===Serie principale===\n{{pokemonimages/head|content=\n', '}}\n\n===Spin-off==='],
    'spinoff': ['===Spin-off===\n{{pokemonimages/head|content=\n', '}}\n\n[[Categoria:Sottopagine immagini Pokémon]]'],
    }
    exceptions = ['Altri', '[[Pokédex Rotom]]', '[[Lugia Ombra]]', '[[Dialga Oscuro]]', '[[Zygarde/Forme|Cellula]]']
    for exception in exceptions:
        delimiter = '{{{{pokemonimages/div|text={}}}}}'.format(exception)
        if delimiter in pagetext:
            delimiters.update({'artwork': ['==Artwork==\n{{pokemonimages/head|content=\n', delimiter],})
    start, end = delimiters[section]
    index1 = pagetext.index(start) + len(start)
    index2 = pagetext.index(end)
    return pagetext[index1:index2]

# update page (all section or given one) and check if it was actually modified
# in that case save it to new text file
def update_page(poke, name, gender, forms, pokelistspath, artsources, singleMS, spsc, rangerdata, goforms, exceptionspath, section, downloadspath, updatespath):
    localfile = os.path.join(downloadspath, '{}.txt'.format(poke))
    if not os.path.isfile(localfile):
        print('File "{}" not found, skipping it.'.format(localfile))
        return
    with open(localfile, 'r') as file:
        pagetext = file.read()
    with open('{}.txt'.format(os.path.join(pokelistspath, poke)), 'r') as pokefile:
        imgs = pokefile.read().splitlines()
    edited = False
    if section in ['artwork', 'all']:
        oldtext = get_section_text(pagetext, 'artwork')
        arts = [img for img in imgs if img.startswith('Artwork')]
        newtext = build_arts(poke, arts, [form[0] for form in forms], gender, artsources, False)
        if newtext != oldtext:
            pagetext = pagetext.replace(oldtext, newtext)
            edited = True
    if section in ['main', 'all']:
        oldtext = get_section_text(pagetext, 'main')
        newtext = build_main(poke, exceptionspath, forms, gender, singleMS, spsc, imgs)
        if newtext != oldtext:
            pagetext = pagetext.replace(oldtext, newtext)
            edited = True
    if section in ['spinoff', 'all']:
        oldtext = get_section_text(pagetext, 'spinoff')
        spinoffimages = get_spinoff_imgs(imgs)
        newtext = build_spinoffs(poke, name, gender, [form[0] for form in forms], spinoffimages, rangerdata, goforms, exceptionspath)
        if newtext != oldtext:
            pagetext = pagetext.replace(oldtext, newtext)
            edited = True
    if edited == True:
        destfile = os.path.join(updatespath, '{}.txt'.format(poke))
        with open(destfile, 'w') as file:
            file.write(pagetext)

parser = argparse.ArgumentParser()
parser.add_argument('--catlistspath', default = 'data/catlists/')
parser.add_argument('--pokelistspath', default = 'data/pokelists/')
parser.add_argument('--pokeformspath', default = 'data/pokeforms/')
parser.add_argument('--exceptionspath', default = 'data/exceptions/')
parser.add_argument('--downloadspath', default = 'data/pokepages-downloaded/')
parser.add_argument('--dexfile', default = 'data/utils/pokes_ndex.txt')
parser.add_argument('--genderdiffsfile', default = 'data/utils/genderdiffs.txt')
parser.add_argument('--genderformsfile', default = 'data/utils/genderforms.txt')
parser.add_argument('--femaleonlyfile', default = 'data/utils/femaleonly.txt')
parser.add_argument('--artsourcesfile', default = 'data/utils/artsources.txt')
parser.add_argument('--singlemsfile', default = 'data/utils/singleMS.txt')
parser.add_argument('--spscfile', default = 'data/utils/spsc.txt')
parser.add_argument('--rangerfile', default = 'data/utils/redirect_ranger.txt')
parser.add_argument('--goformsfile', default = 'data/utils/goforms.txt')
parser.add_argument('--updatepoke', default = '')
parser.add_argument('--section', default = 'all')
parser.add_argument('--updatespath', default = 'data/pokepages-updated/')
parser.add_argument('--upload', default = '')
parser.add_argument('--summary', default = 'Bot: updating Pokémon subpages')
args = parser.parse_args()

if __name__ == '__main__':
    # import data
    getname, genderdiffs, genderforms, femaleonly, artsources, singlemsdata, spscdata, rangerdata, goforms = import_data(args.dexfile, args.genderdiffsfile, args.genderformsfile, args.femaleonlyfile, args.artsourcesfile, args.singlemsfile, args.spscfile, args.rangerfile, args.goformsfile)
    # update pages
    if args.updatepoke:
        if args.updatepoke == 'all':
            lst = os.listdir(args.downloadspath)
        else:
            lst = args.updatepoke.split(',')
        if not os.path.isdir(args.updatespath):
            os.mkdir(args.updatespath)
        for poke in lst:
            gender, singleMS, spsc = get_poke_data(poke, genderdiffs, genderforms, femaleonly, singlemsdata, spscdata)
            forms = get_forms(poke, args.pokeformspath)
            update_page(poke, getname[poke], gender, forms, args.pokelistspath, artsources, singleMS, spsc, rangerdata, goforms, args.exceptionspath, args.section, args.downloadspath, args.updatespath)
    # upload pages
    if args.upload:
        if args.upload == 'all':
            lst = os.listdir(args.updatespath)
        else:
            lst = ['{}.txt'.format(page) for page in args.upload.split(',')]
        site = pywikibot.Site()
        for pokepage in lst:
            localpage = os.path.join(args.updatespath, pokepage)
            wikipage = pywikibot.Page(site, '{}/Immagini'.format(getname[pokepage.replace('.txt', '')]))
            with open(localpage, 'r') as file:
                wikipage.text = file.read()
            wikipage.save(args.summary)
