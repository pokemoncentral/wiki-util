import argparse, os, re

# "convert" english name to italian name
def en_to_it(img, pairs, femaleonly = False, genderform = False):
    # replace Bulba abbrs with PCWiki abbrs
    for pair in pairs:
        img = re.sub(f'{pair[0]}\\b', pair[1], img)
    # "translate" Bulba name to PCWiki name
    img = re.sub(r'HOME(\w+) f s b\.png', r'Homefsh\1 r.png', img)
    img = re.sub(r'HOME(\w+) s b\.png', r'Homemsh\1 r.png', img)
    img = re.sub(r'HOME(\w+) f b\.png', r'Homef\1 r.png', img)
    img = re.sub(r'HOME(\w+) b\.png', r'Homem\1 r.png', img)
    img = re.sub(r'HOME(\w+) f s\.png', r'Homefsh\1.png', img)
    img = re.sub(r'HOME(\w+) s\.png', r'Homemsh\1.png', img)
    img = re.sub(r'HOME(\w+) f\.png', r'Homef\1.png', img)
    img = re.sub(r'HOME(\w+)\.png', r'Homem\1.png', img)
    if femaleonly:
        img = img.replace('Homem', 'Homef')
    if genderform and img.startswith('Homef'):
        img = re.sub(r'^(\w+)\b', r'\1F', img)
    return img

# write missing images to text file
def export_imgs_list(imgslist, filepath):
    if imgslist:
        with open(filepath, 'w') as file:
            file.write('\n'.join(imgslist))

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('--updatecats', default = 'no')
parser.add_argument('--pcwlistn', default = 'data/pokepages-catlists/Modelli Pokémon statici HOME.txt')
parser.add_argument('--pcwlists', default = 'data/pokepages-catlists/Modelli Pokémon statici HOME cromatici.txt')
parser.add_argument('--pcwlistb', default = 'data/pokepages-catlists/Modelli Pokémon statici HOME posteriori.txt')
parser.add_argument('--pcwlistbs', default = 'data/pokepages-catlists/Modelli Pokémon statici HOME posteriori cromatici.txt')
parser.add_argument('--pcwredirects', default = 'data/pokepages-catlists/extra.txt')
parser.add_argument('--bulbafamilyname', default = 'archibulba')
parser.add_argument('--bulbalist', default = 'data/pokepages-utils/home-bulba.txt')
parser.add_argument('--abbrpairs', default = 'data/pokepages-utils/abbr-pairs.txt')
parser.add_argument('--femaleonly', default = 'data/pokepages-utils/femaleonly.txt')
parser.add_argument('--genderforms', default = 'data/pokepages-utils/genderforms.txt')
parser.add_argument('--downloadlistn', default = 'data/pokepages-utils/home-download-normal.txt')
parser.add_argument('--downloadlists', default = 'data/pokepages-utils/home-download-shiny.txt')
parser.add_argument('--downloadlistb', default = 'data/pokepages-utils/home-download-back.txt')
parser.add_argument('--downloadlistbs', default = 'data/pokepages-utils/home-download-back-shiny.txt')
args = parser.parse_args()

# update files with list of HOME images
if args.updatecats == 'yes':
    os.system(f'python3 pwb.py listpages -format:3 -cat:"Modelli Pokémon statici HOME" > "{args.pcwlistn}"')
    os.system(f'python3 pwb.py listpages -format:3 -cat:"Modelli Pokémon statici HOME cromatici" > "{args.pcwlists}"')
    os.system(f'python3 pwb.py listpages -format:3 -cat:"Modelli Pokémon statici HOME posteriori" > "{args.pcwlistb}"')
    os.system(f'python3 pwb.py listpages -format:3 -cat:"Modelli Pokémon statici HOME posteriori cromatici" > "{args.pcwlistbs}"')
    os.system(f'python3 pwb.py listpages -format:3 -cat:"HOME artwork" -family:"{args.bulbafamilyname}" -lang:en > "{args.bulbalist}"')
# retrieve Bulba list and "translate" images
with open(args.abbrpairs, 'r') as file:
    abbrpairs = [line.split(',') for line in file.read().splitlines()]
with open(args.bulbalist, 'r') as file:
    bulbalist = file.read().splitlines()
# retrieve PCWiki lists
with open(args.pcwlistn, 'r') as file:
    pcwlistn = file.read().splitlines()
with open(args.pcwlists, 'r') as file:
    pcwlists = file.read().splitlines()
with open(args.pcwlistb, 'r') as file:
    pcwlistb = file.read().splitlines()
with open(args.pcwlistbs, 'r') as file:
    pcwlistbs = file.read().splitlines()
with open(args.pcwredirects, 'r') as file:
    pcwredirects = file.read().splitlines()
# get list of Pokemon that are always female
with open(args.femaleonly, 'r') as file:
    femaleonlylist = file.read().splitlines()
# get list of Pokemon where female is treated as non-useless form
with open(args.genderforms, 'r') as file:
    genderformslist = file.read().splitlines()
# initialize lists with missing files
downloadlistn = []
downloadlists = []
downloadlistb = []
downloadlistbs = []
# check Bulba images to see what is missing
for bulbaimg in bulbalist:
    ndex = bulbaimg.replace('HOME', '')[:3]
    if ndex in femaleonlylist:
        femaleonly = True
    else:
        femaleonly = False
    if ndex in genderformslist:
        genderform = True
    else:
        genderform = False
    pcwimg = en_to_it(bulbaimg, abbrpairs, femaleonly, genderform)
    if pcwimg.endswith(' r.png'):
        # back model
        if re.search(r'^Home[mf]sh\d', pcwimg) and pcwimg not in pcwlistbs and pcwimg not in pcwredirects:
            downloadlistbs.append(f'{bulbaimg},{pcwimg}') # shiny back model
        elif re.search(r'^Home[mf]\d', pcwimg) and pcwimg not in pcwlistb and pcwimg not in pcwredirects:
            downloadlistb.append(f'{bulbaimg},{pcwimg}') # normal back model
    else:
        # front model
        if re.search(r'^Home[mf]sh\d', pcwimg) and pcwimg not in pcwlists and pcwimg not in pcwredirects:
            downloadlists.append(f'{bulbaimg},{pcwimg}') # shiny front model
        elif re.search(r'^Home[mf]\d', pcwimg) and pcwimg not in pcwlistn and pcwimg not in pcwredirects:
            downloadlistn.append(f'{bulbaimg},{pcwimg}') # normal front model
# write missing images to text files
export_imgs_list(downloadlistn, args.downloadlistn)
export_imgs_list(downloadlists, args.downloadlists)
export_imgs_list(downloadlistb, args.downloadlistb)
export_imgs_list(downloadlistbs, args.downloadlistbs)
