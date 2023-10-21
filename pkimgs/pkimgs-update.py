import pywikibot, argparse, os.path
from scripts.userscripts.pkimgstools import import_ndex, import_data, get_poke_data, get_forms, get_spinoff_imgs, build_arts, build_main, build_spinoffs
'''
Quick infos about variables:
- 'poke' always represents number of Pokédex as string (without form abbr)
- 'pokeabbr' always represents number of Pokédex as string (with form abbr)
- 'ndex' always represents number of Pokédex as integer (without form abbr)
'''

# get text for given section (artworks, main series or spin-offs)
def get_section_text(pagetext, delimiters, section):
    start, end = delimiters[section]
    index1 = pagetext.index(start) + len(start)
    index2 = pagetext.index(end)
    return pagetext[index1:index2]

# update page (all section or given one) and check if it was actually modified
# in that case save it to new text file
def update_page(poke, name, gender, forms, pokelistspath, artsources, singleMS, availdata, rangerdata, goforms, exceptionspath, section, downloadspath, updatespath):
    # get list of abbrs without duplicates
    abbrs = list(dict.fromkeys([form[0] for form in forms]))
    localfile = os.path.join(downloadspath, f'{poke}.txt')
    if not os.path.isfile(localfile):
        print(f'File "{localfile}" not found, skipping it.')
        return
    with open(localfile, 'r') as file:
        pagetext = file.read()
    with open(f'{os.path.join(pokelistspath, poke)}.txt', 'r') as pokefile:
        imgs = pokefile.read().splitlines()
    edited = False
    delimiters = {
    'artwork': ['==Artwork==\n{{pokemonimages/head|content=\n', '}}\n\n==Sprite e modelli=='],
    'main': ['===Serie principale===\n{{pokemonimages/head|content=\n', '}}\n\n===Spin-off==='],
    'spinoff': ['===Spin-off===\n{{pokemonimages/head|content=\n', '}}\n\n[[Categoria:Sottopagine immagini Pokémon]]'],
    }
    if delimiters['main'][1] not in pagetext:
        pagetext = pagetext.replace(delimiters['spinoff'][1], '}}\n\n' + delimiters['spinoff'][0] + '<!--[PLACEHOLDER]-->' + delimiters['spinoff'][1])
    exceptions = ['Altri', '[[Pokédex Rotom]]', '[[Lugia Ombra]]', '[[Dialga Oscuro]]', '[[Zygarde/Forme|Cellula]]']
    for exception in exceptions:
        delimiter = f'{{{{pokemonimages/div|text={exception}}}}}'
        if delimiter in pagetext:
            delimiters.update({'artwork': ['==Artwork==\n{{pokemonimages/head|content=\n', delimiter],})
    if section in ['artwork', 'all']:
        oldtext = get_section_text(pagetext, delimiters, 'artwork')
        arts = [img for img in imgs if img.startswith('Artwork')]
        newtext = build_arts(poke, arts, abbrs, gender, artsources, False)
        if newtext != oldtext:
            pagetext = pagetext.replace(oldtext, newtext)
            edited = True
    if section in ['main', 'all']:
        oldtext = get_section_text(pagetext, delimiters, 'main')
        newtext = build_main(poke, exceptionspath, forms, gender, singleMS, availdata, imgs)
        if newtext != oldtext:
            pagetext = pagetext.replace(oldtext, newtext)
            edited = True
    if section in ['spinoff', 'all']:
        oldtext = get_section_text(pagetext, delimiters, 'spinoff')
        spinoffimages = get_spinoff_imgs(imgs)
        newtext = build_spinoffs(poke, name, gender, abbrs, spinoffimages, rangerdata, goforms, exceptionspath)
        if newtext != oldtext:
            pagetext = pagetext.replace(oldtext, newtext)
            edited = True
    if edited == True:
        destfile = os.path.join(updatespath, f'{poke}.txt')
        with open(destfile, 'w') as file:
            file.write(pagetext)

# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--fam', default = 'encypok')
    parser.add_argument('--lang', default = 'it')
    parser.add_argument('--catlistspath', default = 'data/pokepages-catlists/')
    parser.add_argument('--pokelistspath', default = 'data/pokepages-pokelists/')
    parser.add_argument('--pokeformspath', default = 'data/pokepages-pokeforms/')
    parser.add_argument('--exceptionspath', default = 'data/pokepages-exceptions/')
    parser.add_argument('--downloadspath', default = 'data/pokepages-downloaded/')
    parser.add_argument('--dexfile', default = 'data/pokepages-utils/pokes_names.csv')
    parser.add_argument('--genderdiffsfile', default = 'data/pokepages-utils/genderdiffs.txt')
    parser.add_argument('--genderformsfile', default = 'data/pokepages-utils/genderforms.txt')
    parser.add_argument('--femaleonlyfile', default = 'data/pokepages-utils/femaleonly.txt')
    parser.add_argument('--artsourcesfile', default = 'data/pokepages-utils/artsources.txt')
    parser.add_argument('--singlemsfile', default = 'data/pokepages-utils/singleMS.txt')
    parser.add_argument('--availdir', default = 'data/pokepages-availability')
    parser.add_argument('--rangerfile', default = 'data/pokepages-utils/redirect_ranger.txt')
    parser.add_argument('--goformsfile', default = 'data/pokepages-utils/goforms.txt')
    parser.add_argument('--updatepoke', default = '')
    parser.add_argument('--section', default = 'all')
    parser.add_argument('--updatespath', default = 'data/pokepages-updated/')
    parser.add_argument('--upload', default = '')
    parser.add_argument('--summary', default = 'Bot: updating Pokémon subpages')
    args = parser.parse_args()
    # import data
    getname, getenname, getesname, getdename, getfrname = import_ndex(args.dexfile)
    genderdiffs, genderforms, femaleonly, artsources, singlemsdata, availdata, rangerdata, goforms = import_data(args.genderdiffsfile, args.genderformsfile, args.femaleonlyfile, args.artsourcesfile, args.singlemsfile, args.availdir, args.rangerfile, args.goformsfile)
    # update pages
    if args.updatepoke:
        if args.updatepoke == 'all':
            lst = [poke.replace('.txt', '') for poke in os.listdir(args.downloadspath)]
        else:
            lst = args.updatepoke.split(',')
        if not os.path.isdir(args.updatespath):
            os.mkdir(args.updatespath)
        for poke in lst:
            gender, singleMS = get_poke_data(poke, genderdiffs, genderforms, femaleonly, singlemsdata)
            forms = get_forms(poke, args.pokeformspath)
            update_page(poke, getname[poke], gender, forms, args.pokelistspath, artsources, singleMS, availdata, rangerdata, goforms, args.exceptionspath, args.section, args.downloadspath, args.updatespath)
    # upload pages
    if args.upload:
        if args.upload == 'all':
            lst = os.listdir(args.updatespath)
        else:
            lst = [f'{page}.txt' for page in args.upload.split(',')]
        site = pywikibot.Site(args.lang, fam = args.fam)
        for pokepage in lst:
            localpage = os.path.join(args.updatespath, pokepage)
            wikipage = pywikibot.Page(site, f'{getname[pokepage.replace(".txt", "")]}/Immagini')
            with open(localpage, 'r') as file:
                wikipage.text = file.read()
            wikipage.save(args.summary)

# invoke main function
if __name__ == '__main__':
    main()
