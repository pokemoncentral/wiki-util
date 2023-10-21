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

# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--fam', default = 'encypok')
    parser.add_argument('--updatecats', default = 'no')
    parser.add_argument('--pcwlist', default = 'data/pokepages-catlists/Modelli statici Pokémon HOME.txt')
    parser.add_argument('--pcwredirects', default = 'data/pokepages-catlists/extra.txt')
    parser.add_argument('--bulbafamilyname', default = 'archibulba')
    parser.add_argument('--bulbalist', default = 'data/pokepages-utils/home-bulba.txt')
    parser.add_argument('--abbrpairs', default = 'data/pokepages-utils/abbr-pairs.txt')
    parser.add_argument('--femaleonly', default = 'data/pokepages-utils/femaleonly.txt')
    parser.add_argument('--genderforms', default = 'data/pokepages-utils/genderforms.txt')
    parser.add_argument('--downloadlist', default = 'data/pokepages-utils/home-download.txt')
    args = parser.parse_args()
    # update files with list of HOME images
    if args.updatecats == 'yes':
        os.system(f'python3 pwb.py listpages -format:3 -cat:"Modelli statici Pokémon HOME" -family:"{args.fam}" -lang:it > "{args.pcwlist}"')
        os.system(f'python3 pwb.py listpages -format:3 -cat:"HOME artwork" -family:"{args.bulbafamilyname}" -lang:en > "{args.bulbalist}"')
    # retrieve Bulba list and "translate" images
    with open(args.abbrpairs, 'r') as file:
        abbrpairs = [line.split(',') for line in file.read().splitlines()]
    with open(args.bulbalist, 'r') as file:
        bulbalist = file.read().splitlines()
    # retrieve PCWiki lists
    with open(args.pcwlist, 'r') as file:
        pcwlist = file.read().splitlines()
    with open(args.pcwredirects, 'r') as file:
        pcwredirects = file.read().splitlines()
    pcwlist = pcwlist + pcwredirects
    # get list of Pokemon that are always female
    with open(args.femaleonly, 'r') as file:
        femaleonlylist = file.read().splitlines()
    # get list of Pokemon where female is treated as non-useless form
    with open(args.genderforms, 'r') as file:
        genderformslist = file.read().splitlines()
    # initialize lists with missing files
    downloadlist = []
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
        if pcwimg not in pcwlist:
            downloadlist.append(f'{bulbaimg},{pcwimg}')
    # write missing images to text files
    export_imgs_list(downloadlist, args.downloadlist)

# invoke main function
if __name__ == '__main__':
    main()
