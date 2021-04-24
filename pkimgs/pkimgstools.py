import pywikibot, argparse, os, os.path, re
from math import floor
'''
Quick infos about variables:
- 'poke' always represents number of Pokédex as string (without form abbr)
- 'pokeabbr' always represents number of Pokédex as string (with form abbr)
- 'ndex' always represents number of Pokédex as integer (without form abbr)
'''
# dict to map games to "generation" (remember to keep updated)
# non-integers are used for things introduced in the middle of a generation
gametogen = {
'verde': 1,
'rb': 1,
'gia': 1,
'oa': 2,
'or': 2,
'ar': 2,
'cr': 2,
'rz': 3,
'rfvf': 3.1,
'sme': 3.2,
'dp': 4,
'pt': 4.1,
'hgss': 4.2,
'nb': 5,
'nb2': 5.1,
'xy': 6,
'roza': 6.1,
'sl': 7,
'usul': 7.1,
'lgpe': 7.2,
'spsc': 8,
'dlps': 8.1,
'lpa': 8.2,
}

# dict to map ndex to name
def import_ndex(dexfile):
    getname = {}
    with open(dexfile, 'r') as file:
        for line in file:
            items = line.strip().split(',')
            getname.update({items[0]: items[1]})
    return getname

# import various useful data
def import_data(dexfile, genderdiffsfile, genderformsfile, femaleonlyfile, artsourcesfile, singlemsfile, spscfile, rangerfile, goformsfile):
    getname = import_ndex(dexfile)
    # import other data
    with open(genderdiffsfile, 'r') as file:
        genderdiffs = file.read().splitlines()
    with open(genderformsfile, 'r') as file:
        genderforms = file.read().splitlines()
    with open(femaleonlyfile, 'r') as file:
        femaleonly = file.read().splitlines()
    with open(artsourcesfile, 'r') as file:
        artsources = file.read().splitlines()
    with open(spscfile, 'r') as file:
        spscdata = file.read().splitlines()
    with open(singlemsfile, 'r') as file:
        singlemsdata = file.read().splitlines()
    with open(rangerfile, 'r') as file:
        rangerdata = file.read().splitlines()
    with open(goformsfile, 'r') as file:
        goforms = file.read().splitlines()
    return getname, genderdiffs, genderforms, femaleonly, artsources, singlemsdata, spscdata, rangerdata, goforms

# get data for given Pokémon
def get_poke_data(poke, genderdiffs, genderforms, femaleonly, singlemsdata, spscdata):
    if poke in genderdiffs:
        gender = 'both'
    elif poke in genderforms:
        gender = 'bothforms'
    elif poke in femaleonly:
        gender = 'f'
    else:
        gender = ''
    if poke in singlemsdata:
        singleMS = True
    else:
        singleMS = False
    if poke in spscdata:
        spsc = True
    else:
        spsc = False
    return gender, singleMS, spsc

# get list of alternative forms for given Pokémon
def get_forms(poke, formspath):
    ndex = int(poke)
    last = max(gametogen, key = gametogen.get)
    formsfile = os.path.join(formspath, '{}.txt'.format(poke))
    # alternative forms
    if os.path.isfile(formsfile):
        forms = []
        with open(formsfile, 'r') as file:
            for line in file:
                # examples of lines: ",oa," "M,xy,usul"
                abbr, since, until = line.strip().split(',')
                if until == '':
                    until = last
                forms.append([abbr, since, until])
    # single form (remember to keep updated)
    else:
        if ndex <= 151:
            forms = [['', 'rb', last]]
        elif ndex <= 251:
            forms = [['', 'oa', last]]
        elif ndex <= 386:
            forms = [['', 'rz', last]]
        elif ndex <= 493:
            forms = [['', 'dp', last]]
        elif ndex <= 649:
            forms = [['', 'nb', last]]
        elif ndex <= 721:
            forms = [['', 'xy', last]]
        elif ndex <= 802:
            forms = [['', 'sl', last]]
        elif ndex <= 807:
            forms = [['', 'usul', last]]
        elif ndex <= 898:
            forms = [['', 'spsc', last]]
    return forms

# get all artworks for given form
def insert_arts(pokeabbr, arts, shiny, sources):
    text = ''
    for source in sources:
        # handle these two special cases
        if source == 'PMDDX' and pokeabbr in ['025', '133']:
            text += '|PMDDX=2\n'
            arts.remove('Artwork{}m PMDDX.png'.format(pokeabbr))
            arts.remove('Artwork{}f PMDDX.png'.format(pokeabbr))
        else:
            # build name of artwork
            art = 'Artwork{} '.format(pokeabbr)
            if shiny == True:
                art += 'cromatico '
            art += '{}.png'.format(source)
            if art in arts:
                # parameter of template pokemonimages/artworks
                sourceabbr = source.replace(' ', '').replace('é', 'e')
                # add found artwork to page and remove it from list of artworks
                # this is needed to retrieve artworks don't have standard name
                # they will be added separately and have to be handled manually
                arts.remove(art)
                counter = 1
                art = art.replace('.png', ' 1.png')
                found = True
                # count number of artworks of given form from this source
                while found == True:
                    art = re.sub(r' \d+\.png', r' {}.png'.format(counter + 1), art)
                    if art in arts:
                        arts.remove(art)
                        counter += 1
                    else:
                        found = False
                text += '|{}={}\n'.format(sourceabbr, counter)
    return text, arts

# insert piece of template with artworks of given form
# if previous function returns non-empty text, return pokemonimages/artworks
# otherwise nothing is done and empty text is returned
def build_form_arts(pokeabbr, form, arts, sources):
    if len([art for art in arts if 'Artwork{} cromatico'.format(pokeabbr) in art]) > 0:
        shinies = True
    else:
        shinies = False
    newtext, arts = insert_arts(pokeabbr, arts, False, sources)
    if newtext:
        text = '{{{{pokemonimages/artworks\n|ndex={}\n'.format(pokeabbr)
        if form == True:
            text += '|form=yes\n'
        if shinies == True:
            text += '|shiny=no\n'
        text += newtext
        if shinies == True:
            if form == True:
                text += '}}}}\n{{{{pokemonimages/artworks\n|ndex={}\n|form=yes\n|shiny=yes\n'.format(pokeabbr)
            else:
                text += '}}}}\n{{{{pokemonimages/artworks\n|ndex={}\n|shiny=yes\n'.format(pokeabbr)
            newtext, arts = insert_arts(pokeabbr, arts, True, sources)
            text += newtext
        text += '}}\n'
    else:
        text = ''
    return text, arts

# build entire content of artworks box for given Pokémon
def build_arts(poke, arts, abbrs, gender, sources, extras):
    # no alternative forms
    if len(abbrs) == 1:
        text, arts = build_form_arts(poke, False, arts, sources)
    # add all forms
    else:
        text = ''
        for abbr in abbrs:
            newtext, arts = build_form_arts(poke + abbr, True, arts, sources)
            text += newtext
    # fix gender differences treated as useless forms
    if abbrs[:2] == ['', 'F'] and gender == 'both':
        text = text.replace('|form=yes'.format(poke), '|gender=m\n|bothgenders=yes', 1)
        text = text.replace('|form=yes'.format(poke), '|gender=f\n|bothgenders=yes', 1)
    # unused arts (those with non-standard names)
    if extras == True and arts != []:
        text += '\n{{pokemonimages/div|text=Altri}}\n'
        for art in arts:
            text += '{{{{pokemonimages/entry\n|xl=20|md=25|sm=33|xs=50\n|img={}\n|size=x150px\n|downdesc= (artwork da [[]]) }}}}\n'.format(art)
    return text

# build a single pokemonimages/main* for a single form
def build_main_gen_entry(pokeabbr, gen, form = False, since = '', female = False, bothgenders = False, gen4common = ''):
    text = '{{{{pokemonimages/main{}|ndex={}'.format(gen, pokeabbr)
    if form == True:
        text += '|form=yes'
    if since:
        text += '|since={}'.format(since)
    if female == True:
        text += '|gender=f'
    if bothgenders == True:
        text += '|bothgenders=yes'
    # some Pokémon have same sprites in DPPt or PtHGSS or all games
    if gen == '4' and gen4common:
        text += '|{}=yes'.format(gen4common)
    text += '}}'
    return text

# build all pokemonimages/main* entries for given Pokémon in given generation
def build_main_gen(poke, gen, forms, gender = '', gen4sprites = []):
    text = '{{{{pokemonimages/group|gen={}|content=\n'.format(gen)
    # search for other forms that esist in given generation
    numgen = int(gen)
    if len([form for form in forms if floor(gametogen[form[1]]) <= numgen and numgen <= gametogen[form[2]]]) > 1:
        multiform = True
    else:
        multiform = False
    # gender differences treated as useless forms
    if [form[0] for form in forms[:2]] == ['', 'F'] and gender == 'both':
        text += '{}\n'.format(build_main_gen_entry(poke, gen, form = False, bothgenders = True))
        text += '{}\n'.format(build_main_gen_entry(poke, gen, form = False, female = True, bothgenders = True))
        if len(forms) > 2:
            forms = forms[2:]
        else:
            forms = []
    # gender differences treated as alt forms
    elif [form[0] for form in forms[:2]] == ['', 'F'] and gender == 'bothforms':
        text += '{}\n'.format(build_main_gen_entry(poke, gen, form = True))
        text += '{}\n'.format(build_main_gen_entry(poke, gen, form = True, female = True))
        if len(forms) > 2:
            forms = forms[2:]
        else:
            forms = []
    # other cases
    for form in forms:
        abbr, since, until = form
        if gen == '4':
            pokeabbr = poke + abbr
            # Registeel is a special case, because Sprdpm379.png is only referred to japanese DP
            if pokeabbr == '379':
                gen4common = 'all'
            else:
                # search for common sprites in generation 4
                gen4 = ''
                if 'Sprdpm{}.png'.format(pokeabbr) in gen4sprites or 'Sprdpf{}.png'.format(pokeabbr) in gen4sprites:
                    gen4 += 'dp'
                if 'Sprptm{}.png'.format(pokeabbr) in gen4sprites or 'Sprptf{}.png'.format(pokeabbr) in gen4sprites:
                    gen4 += 'pt'
                if 'Sprhgssm{}.png'.format(pokeabbr) in gen4sprites or 'Sprhgssf{}.png'.format(pokeabbr) in gen4sprites:
                    gen4 += 'hgss'
                if gen4 == 'dp':
                    gen4common = 'all'
                elif gen4 in ['dppt', 'pt']:
                    gen4common = 'pthgss'
                elif gen4 == 'dphgss':
                    gen4common = 'dppt'
                else:
                    gen4common = ''
        else:
            gen4common = ''
        # Maybe the following part can be done better, but it works and I don't want to break it
        if abbr == '':
            # gender differences
            if gender == 'both':
                text += '{}\n'.format(build_main_gen_entry(poke, gen, form = False, bothgenders = True, gen4common = gen4common))
                text += '{}\n'.format(build_main_gen_entry(poke, gen, form = False, female = True, bothgenders = True, gen4common = gen4common))
            # female only
            elif gender == 'f':
                text += '{}\n'.format(build_main_gen_entry(poke, gen, form = multiform, female = True, gen4common = gen4common))
            # other cases
            else:
                # check if was introduced in the middle of the generation
                if numgen < gametogen[since] and gametogen[since] < numgen + 1:
                    text += '{}\n'.format(build_main_gen_entry(poke, gen, form = multiform, since = since, female = False, gen4common = gen4common))
                else:
                    text += '{}\n'.format(build_main_gen_entry(poke, gen, form = multiform, gen4common = gen4common))
        elif abbr == 'F' and gender == 'both':
            pass  # already done
        elif floor(gametogen[since]) <= numgen and numgen <= gametogen[until]:
            if gender == 'f':
                female = True
            else:
                female = False
            if numgen < gametogen[since] and gametogen[since] < numgen + 1:
                text += '{}\n'.format(build_main_gen_entry(poke + abbr, gen, form = True, since = since, female = female, gen4common = gen4common))
            else:
                text += '{}\n'.format(build_main_gen_entry(poke + abbr, gen, form = True, female = female, gen4common = gen4common))
    text += '}}\n'
    return text

# build mini sprites entry for given form
def build_ms_entry(poke, form, multiform, spsc, genderform = ''):
    # dicts to map introduction to pokemonimages/mainMS parameter values
    ms345 = {
    3: '345',
    4: '45',
    5: '5',
    4.1: 'pt',
    4.2: 'hgss',
    5.1: 'nb2',
    }
    ms67 = {
    6: '67',
    7: '7',
    6.1: 'roza',
    7.1: 'usul',
    7.2: 'lgpe',
    }
    abbr, since, until = form
    pokeabbr = poke + abbr
    if pokeabbr == '493Sc':
        text = ''
    else:
        start = gametogen[since]
        end = gametogen[until]
        ndex = int(poke)
        text = '{{{{pokemonimages/mainMS|ndex={}'.format(pokeabbr)
        if genderform:
            text += '|bothgenders=yes|gender={}'.format(genderform)
        if start <= 1:
            text += '|ms1=yes'
        if start <= 2:
            text += '|ms2=yes'
        if floor(start) <= 5:
            text += '|ms345={}'.format(ms345.get(start, '345'))
        if floor(start) <= 7 and end >= 6:
            if end < 7:
                text += '|ms67=rozaonly'
            else:
                text += '|ms67={}'.format(ms67.get(start, '67'))
        if spsc == True and end >= 8:
            text += '|ms8=yes'
        if multiform == True:
            text += '|form=yes'
            # these forms don't have an overworld sprite in HGSS
            if pokeabbr in ['351S', '351P', '351N', '421S']:
                text += '|overworld=no'
        text += '}}\n'
    return text

# build main series entries
def build_main(poke, exceptionspath, forms, gender, singleMS, spsc, imgs):
    ndex = int(poke)
    text = ''
    # check for exception
    exceptionfile = os.path.join(exceptionspath, '{}_main.txt'.format(poke))
    if os.path.isfile(exceptionfile):
        with open(exceptionfile, 'r') as file:
            text += file.read()
    else:
        if ndex <= 151:
            text += build_main_gen(poke, '1', forms)
        if ndex <= 251:
            text += build_main_gen(poke, '2', forms)
        if ndex <= 385:
            text += build_main_gen(poke, '3', forms)
        if ndex == 386:
            with open(os.path.join(exceptionspath, '{}_main3.txt'.format(poke)), 'r') as file:
                text += file.read().strip()
        if ndex <= 493:
            gen4sprites = [img for img in imgs if re.search(r'^Spr(dp|pt|hgss)', img)]
            text += build_main_gen(poke, '4', forms, gender, gen4sprites)
        if ndex <= 649:
            text += build_main_gen(poke, '5', forms, gender)
        if ndex <= 721:
            text += build_main_gen(poke, '6', forms, gender)
        if ndex <= 807:
            text += build_main_gen(poke, '7', forms, gender)
        #if ndex <= 898:
        if spsc == True:
            text += build_main_gen(poke, '8', forms, gender)
        # mini sprites
        text += '{{pokemonimages/group|gen=MS|content=\n'
        # check for exception
        exceptionfile = os.path.join(exceptionspath, '{}_mainMS.txt'.format(poke))
        if os.path.isfile(exceptionfile):
            with open(exceptionfile, 'r') as file:
                text += file.read()
        else:
            if singleMS == True:
                text += build_ms_entry(poke, forms[0], False, spsc)
            else:
                if len(forms) > 1:
                    multiform = True
                else:
                    multiform = False
                if [form[0] for form in forms[:2]] == ['', 'F'] and gender == 'both':
                    text += build_ms_entry(poke, forms[0], False, spsc, genderform = 'm')
                    text += build_ms_entry(poke, forms[1], False, spsc, genderform = 'f')
                    if len(forms) > 2:
                        for form in forms[2:]:
                            text += build_ms_entry(poke, form, multiform, spsc)
                else:
                    for form in forms:
                        text += build_ms_entry(poke, form, multiform, spsc)
        text += '}}\n'
    return text

# remove artworks and main series sprites/models from list
def get_spinoff_imgs(imgs):
    maingames = r'{}'.format('|'.join([game for game in gametogen]))
    exclude = r'^(Artwork|ConceptArt|Spr({})|(Ani)?\d\d\d\w{{0,2}}MS)'.format(maingames)
    #exclude = r'^(Artwork|ConceptArt|Spr(' + maingames + ')[mf]?d?(sh)?\d|(Ani)?\d\d\d\w{0,2}MS)'
    return [img for img in imgs if not re.search(exclude, img)]

# build spin-offs content
def build_spinoffs(poke, name, gender, abbrs, imgs, rangerdata, goforms, exceptionspath):
    texts = []
    finaltext = ''
    if abbrs[:2] == ['', 'F'] and gender == 'both':
        uselessgender = True
    else:
        uselessgender = False
    for abbr in abbrs:
        pokeabbr = poke + abbr
        formtext = ''
        # Stadium
        if 'Sprstad{}.png'.format(pokeabbr) in imgs:
            formtext += '|stadium=StS2\n'
        elif 'Sprstad2{}.png'.format(pokeabbr) in imgs:
            formtext += '|stadium=S2\n'
        if len(pokeabbr) == 3:
            # TCG
            tcg1search = r'TCG1 (...) {}\.png'.format(name)
            tcg2search = r'TCG2 (...) {}\.png'.format(name)
            tcg1 = [img for img in imgs if re.search(tcg1search, img)]
            tcg2 = [img for img in imgs if re.search(tcg2search, img)]
            for j in range(len(tcg1)):
                formtext += '|tcg1-{}={}\n'.format(j + 1, re.sub(tcg1search, r'\1', tcg1[j])).replace('-1', '')
            for j in range(len(tcg2)):
                formtext += '|tcg2-{}={}\n'.format(j + 1, re.sub(tcg2search, r'\1', tcg2[j])).replace('-1', '')
            # extras
            if name not in ['Clefairy', 'Jynx']:
                extratcg2 = [img for img in imgs if img.startswith('TCG2') and name in img and not re.search(tcg2search, img)]
                if len(extratcg2) > 0:
                    darksearch = r'TCG2 (...) Dark {}\.png'.format(name)
                    extrasearch = r'TCG2 (...) (.+) {}\.png'.format(name)
                    dark = False
                    for item in extratcg2:
                        if re.search(darksearch, item):
                            if dark == False:
                                formtext += '|darktcg2={}\n'.format(re.sub(darksearch, r'\1', item))
                                dark = True
                            else:
                                formtext += '|darktcg2-2={}\n'.format(re.sub(darksearch, r'\1', item))
                        elif re.search(extrasearch, item):
                            formtext += '|extratcg2={}\n'.format(re.sub(extrasearch, r'\1', item))
                            formtext += '|extratcg2name={}\n'.format(re.sub(extrasearch, r'\2', item))
            # Pinball
            pinball = ''
            if 'Pin{}.png'.format(pokeabbr) in imgs:
                pinball += 'rb'
            if 'PinRZ{}.png'.format(pokeabbr) in imgs:
                pinball += 'rz'
            if 'Pinani{}.gif'.format(pokeabbr) in imgs or 'PinRZani{}.gif'.format(pokeabbr) in imgs:
                pinball += 'double'
            else:
                pinball += 'single'
            if pinball.replace('single', ''):
                formtext += '|pinball={}\n'.format(pinball)
            # Puzzle Challenge
            if 'PuzzleChallenge{}.png'.format(pokeabbr) in imgs:
                formtext += '|puzzlechallenge=yes\n'
        # Auros
        if 'Sprcolo{}.png'.format(pokeabbr) in imgs:
            formtext += '|auros=coloxd\n'
        elif 'Sprxdsh{}.png'.format(pokeabbr) in imgs:
            formtext += '|auros=xd\n'
        elif 'Sprxd{}.png'.format(pokeabbr) in imgs:
            formtext += '|auros=xdsingle\n'
        # Dash
        if 'Dash{}.png'.format(pokeabbr) in imgs:
            formtext += '|dash=yes\n'
        # Link
        if 'Linkani{}.gif'.format(pokeabbr) in imgs and 'LB{}.png'.format(pokeabbr) in imgs:
            formtext += '|link=both\n'
        elif 'Linkani{}.gif'.format(pokeabbr) in imgs:
            formtext += '|link=link\n'
        elif 'LB{}.png'.format(pokeabbr) in imgs:
            formtext += '|link=battle\n'
        # Team Turbo
        if 'TeamTurbo{}.png'.format(pokeabbr) in imgs:
            formtext += '|teamturbo=yes\n'
        # Mystery Dungeon
        if 'MDSprrb{}.png'.format(pokeabbr) in imgs:
            formtext += '|mdrbtoc=rbtoc\n'
        elif 'MDSprtoc{}.png'.format(pokeabbr) in imgs:
            if pokeabbr in ['487O', '492', '492C']:
                formtext += '|mdrbtoc=c\n'
            else:
                formtext += '|mdrbtoc=toc\n'
        if 'MDPPSI{}.png'.format(pokeabbr) in imgs:
            formtext += '|mdpsi=yes\n'
        if 'MDPSuper{}.png'.format(pokeabbr) in imgs:
            formtext += '|mdsuper=yes\n'
        mddx = ''
        if 'MDPDX{}.png'.format(pokeabbr) in imgs:
            mddx += 'mn'
        if 'MDPDX{} f.png'.format(pokeabbr) in imgs:
            mddx += 'fn'
        if 'MDPDXsh{}.png'.format(pokeabbr) in imgs:
            mddx += 'msh'
        if 'MDPDXsh{} f.png'.format(pokeabbr) in imgs:
            mddx += 'fsh'
        if mddx:
            formtext += '|mddx={}\n'.format(mddx)
        mddxmini = ''
        if 'MDSprdx{}.png'.format(pokeabbr) in imgs:
            mddxmini += 'mn'
        if 'MDSprdx{} f.png'.format(pokeabbr) in imgs:
            mddxmini += 'fn'
        if 'MDSprdx{} sh.png'.format(pokeabbr) in imgs:
            mddxmini += 'msh'
        if 'MDSprdx{} f sh.png'.format(pokeabbr) in imgs:
            mddxmini += 'fsh'
        if mddxmini:
            formtext += '|mddxmini={}\n'.format(mddxmini)
        # Ranger
        ranger1 = 'Sprranger{}.png'.format(pokeabbr)
        ranger2 = 'Sprrangerosa{}.png'.format(pokeabbr)
        ranger3 = 'Sprrangertdl{}.png'.format(pokeabbr)
        if ranger1 in imgs:
            ranger = 'ranger1'
            if '{} > {}'.format(ranger2, ranger1) in rangerdata:
                ranger += '2'
            if '{} > {}'.format(ranger3, ranger1) in rangerdata:
                ranger += '3'
            formtext += '|{}=yes\n'.format(ranger)
        if ranger2 in imgs:
            ranger = 'ranger2'
            if '{} > {}'.format(ranger3, ranger2) in rangerdata:
                ranger += '3'
            formtext += '|{}=yes\n'.format(ranger)
        if ranger3 in imgs:
            formtext += '|ranger3=yes\n'
        if re.search(r'(\|ranger\d\d=yes\n\|ranger\d=yes|\|ranger\d=yes\n\|ranger\d\d=yes)', formtext):
            print(pokeabbr)
        # Battle Revolution
        if 'PBR{}.png'.format(pokeabbr) in imgs:
            formtext += '|pbr=single\n'
        elif 'PBR{}m.png'.format(pokeabbr) in imgs and 'PBR{}f.png'.format(pokeabbr) in imgs:
            formtext += '|pbr=both\n'
        # Rumble
        rumble = ''
        if 'SPR{}.png'.format(pokeabbr) in imgs:
            rumble += '2'
        if 'PRW{}.png'.format(pokeabbr) in imgs:
            rumble += '4'
        if 'Rush{} f.png'.format(pokeabbr) in imgs:
            rumble += '5g'
        elif 'Rush{}.png'.format(pokeabbr) in imgs:
            rumble += '5'
        if rumble:
            formtext += '|rumble={}\n'.format(rumble)
        # PokéPark
        if 'PPWM{}.png'.format(pokeabbr) in imgs:
            formtext += '|pokepark=both\n'
        elif 'PPW{}.png'.format(pokeabbr) in imgs or 'PP2{}.png'.format(pokeabbr) in imgs:
            formtext += '|pokepark=sprite\n'
        # Dream World
        if 'PDW{}.png'.format(pokeabbr) in imgs:
            formtext += '|pdw=yes\n'
        # Impara con Pokémon
        if 'ICP{}.png'.format(pokeabbr) in imgs:
            formtext += '|icp=yes\n'
        # Conquest
        if 'PCP{}.png'.format(pokeabbr) in imgs:
            formtext += '|cq=yes\n'
        # Pokédex 3D Pro
        if 'P3P{}.png'.format(pokeabbr) in imgs:
            formtext += '|p3p=yes\n'
        # Shuffle
        if 'Shuffle{}.png'.format(pokeabbr) in imgs:
            formtext += '|shuffle=yes\n'
            if 'Shuffle{}cr.png'.format(pokeabbr) in imgs:
                formtext += '|shufflecr=yes\n'
            if 'Shuffle{}oc.png'.format(pokeabbr) in imgs:
                formtext += '|shuffleoc=yes\n'
            if 'Shuffle{}im.png'.format(pokeabbr) in imgs:
                formtext += '|shuffleim=yes\n'
            if 'Shuffle{}fe.png'.format(pokeabbr) in imgs:
                formtext += '|shufflefe=yes\n'
            if 'Shuffle{}boss.png'.format(pokeabbr) in imgs:
                formtext += '|shuffleboss=yes\n'
        # Super Mario maker
        if 'SMM{}.png'.format(pokeabbr) in imgs:
            formtext += '|smm=yes\n'
        # Picross
        if 'Picross{}.png'.format(pokeabbr) in imgs:
            formtext += '|picross=yes\n'
        # Duel
        duel = [img for img in imgs if re.search(r'Duel(sh)?{}\b'.format(pokeabbr), img)]
        if duel != []:
            counter = 1
            for img in duel:
                if not img.startswith('Duelsh'):
                    formtext += '|duel{}={}\n'.format(str(counter).replace('1', ''), re.sub(r'Duel\d\d\d\w?\w?\-(\d+)\.png', r'\1', img))
                    counter += 1
                else:
                    formtext += '|duelsh={}\n'.format(re.sub(r'Duelsh\d\d\d\w?\w?\-(\d+)\.png', r'\1', img))
        # GO
        if 'GO{} f s.png'.format(pokeabbr) in imgs:
            formtext += '|go=shinyboth\n'
        elif 'GO{} s.png'.format(pokeabbr) in imgs:
            formtext += '|go=shiny\n'
        elif 'GO{} f.png'.format(pokeabbr) in imgs:
            formtext += '|go=both\n'
        elif 'GO{}.png'.format(pokeabbr) in imgs:
            formtext += '|go=normal\n'
        # Magikarp Jump
        if 'MJ{}.png'.format(pokeabbr) in imgs:
            formtext += '|mj=yes\n'
        # Casetta dei Pokémon
        if 'CDP{}.png'.format(pokeabbr) in imgs:
            formtext += '|cdp=yes\n'
        # Detective Pikachu
        if 'DetectivePikachu{}.png'.format(pokeabbr) in imgs:
            formtext += '|dp=yes\n'
        # Quest
        if 'QuestSpr{}.png'.format(pokeabbr) in imgs:
            formtext += '|quest=yes\n'
        # Masters
        if 'MastersEX{}f.png'.format(pokeabbr) in imgs:
            formtext += '|mastersnormal=both\n'
        elif 'MastersEX{}.png'.format(pokeabbr) in imgs:
            formtext += '|mastersnormal=single\n'
        if 'MastersEXsh{}f.png'.format(pokeabbr) in imgs:
            formtext += '|mastersshiny=both\n'
        elif 'MastersEXsh{}.png'.format(pokeabbr) in imgs:
            formtext += '|mastersshiny=single\n'
        if 'MastersIcona{} f.png'.format(pokeabbr) in imgs:
            formtext += '|mastersmugshot=both\n'
        elif 'MastersIcona{}.png'.format(pokeabbr) in imgs:
            formtext += '|mastersmugshot=single\n'
        # HOME
        # gender differences treated as useless forms need some fixes
        if uselessgender == True and abbr in ['', 'F']:
            if abbr == '':
                if 'Homemsh{}.png'.format(poke) in imgs:
                    formtext += '|home=shiny\n'
                elif 'Homem{}.png'.format(poke) in imgs:
                    formtext += '|home=normal\n'
            else:
                if 'Homemsh{}.png'.format(poke) in imgs:
                    formtext += '|home=shinyfemale\n'
                elif 'Homem{}.png'.format(poke) in imgs:
                    formtext += '|home=normalfemale\n'
        else:
            if 'Homemsh{}.png'.format(pokeabbr) in imgs and 'Homefsh{}.png'.format(pokeabbr) in imgs:
                formtext += '|home=shinyboth\n'
            elif 'Homefsh{}.png'.format(pokeabbr) in imgs:
                formtext += '|home=shinyfemale\n'
            elif 'Homemsh{}.png'.format(pokeabbr) in imgs:
                formtext += '|home=shiny\n'
            elif 'Homem{}.png'.format(pokeabbr) in imgs and 'Homef{}.png'.format(pokeabbr) in imgs:
                formtext += '|home=normalboth\n'
            elif 'Homef{}.png'.format(pokeabbr) in imgs:
                formtext += '|home=normalfemale\n'
            elif 'Homem{}.png'.format(pokeabbr) in imgs:
                formtext += '|home=normal\n'
        # Smile
        if 'Smile{}.png'.format(pokeabbr) in imgs:
            formtext += '|smile=yes\n'
        if 'SmileCostume{} 4.png'.format(pokeabbr) in imgs:
            formtext += '|smilecostume=4\n'
        elif 'SmileCostume{} 2.png'.format(pokeabbr) in imgs:
            formtext += '|smilecostume=2\n'
        if 'SmileIcona{}.png'.format(pokeabbr) in imgs:
            formtext += '|smileicona=yes\n'
        if 'SmileDormiente{}.png'.format(pokeabbr) in imgs:
            formtext += '|smiledormiente=yes\n'
        if 'SmileConsiglio{}.png'.format(pokeabbr) in imgs:
            formtext += '|smileconsiglio=yes\n'
        if pokeabbr in ['007', '025', '133']:
            extra = [img for img in imgs if re.search(r'Smile(.*){}'.format(name), img)]
            counter = 0
            for img in extra:
                counter += 1
                formtext += '|smileextra{}={}\n'.format(str(counter).replace('1', ''), re.sub(r'SmileCostume (.+)\.png', r'\1', img))
        # Café Mix
        cafemix = ''
        if 'CafeMixSprite{} staff.png'.format(pokeabbr) in imgs:
            cafemix += 's'
        if 'CafeMixSprite{} guest.png'.format(pokeabbr) in imgs:
            cafemix += 'g'
        if 'CafeMixSprite{} tassello.png'.format(pokeabbr) in imgs:
            cafemix += 't'
        if cafemix:
            formtext += '|cafemix={}\n'.format(cafemix)
        # add only if there are entries for this form
        if formtext:
            texts.append([pokeabbr, formtext])
    if len(texts) > 1:
        for text in texts:
            finaltext += '{{{{pokemonimages/spinoff\n|ndex={}\n|form=yes\n{}}}}}\n'.format(text[0], text[1])
        # fix gender differences treated as useless forms
        if uselessgender == True:
            finaltext = finaltext.replace('|form=yes'.format(poke), '|gender=m\n|bothgenders=yes', 1)
            finaltext = finaltext.replace('|form=yes'.format(poke), '|gender=f\n|bothgenders=yes', 1)
    elif len(texts) == 1:
        finaltext = '{{{{pokemonimages/spinoff\n|ndex={}\n{}}}}}\n'.format(texts[0][0], texts[0][1])
    # extras for Pikachu and Magikarp
    if poke == '025':
        with open(os.path.join(exceptionspath, '025_extraTCG.txt'), 'r') as file:
            finaltext += file.read()
        with open(os.path.join(exceptionspath, '025_extraShuffle.txt'), 'r') as file:
            finaltext += file.read()
    elif poke == '129':
        with open(os.path.join(exceptionspath, '129_extraMJ.txt'), 'r') as file:
            finaltext += file.read()
    # GO extras
    extrago = ''
    for goform in goforms:
        if 'GO{} {}.png'.format(poke, goform) in imgs:
            if 'GO{} {} f.png'.format(poke, goform) in imgs:
                if 'GO{} {} s.png'.format(poke, goform) in imgs:
                    text = 'shinyboth'
                else:
                    text = 'both'
            else:
                if 'GO{} {} s.png'.format(poke, goform) in imgs:
                    text = 'shiny'
                else:
                    text = 'normal'
            extrago += '|{}={}\n'.format(goform.lower(), text)
    if extrago:
        finaltext += '{{{{pokemonimages/extraGO\n|ndex={}\n{}}}}}\n'.format(poke, extrago)
    # MDDX extras
    search = r'MDPDX{}\-(\w+)\.png'.format(poke)
    extramddx = [img for img in imgs if re.search(search, img)]
    if len(extramddx) > 0:
        extras = [re.sub(search, r'\1', img) for img in extramddx]
        finaltext += '{{{{pokemonimages/extraMDDX|ndex={}|{}}}}}\n'.format(poke, '|'.join(extras))
    # Café Mix extras
    cmfile = os.path.join(exceptionspath, '{}_extraCM.txt'.format(poke))
    if os.path.isfile(cmfile):
        with open(cmfile, 'r') as file:
            finaltext += file.read()
    return finaltext

# build wikicode of page for given Pokémon
def build_poke_page(poke, name, pokelistspath, pagespath, formspath, artsources, goforms, exceptionspath, gender, singleMS, spsc, rangerdata, dename, frname):
    # get alternative forms
    forms = get_forms(poke, formspath)
    # get list of images of given Pokémon
    with open('{}.txt'.format(os.path.join(pokelistspath, poke)), 'r') as pokefile:
        imgs = pokefile.read().splitlines()
    # artworks
    arts = [img for img in imgs if img.startswith('Artwork')]
    pagetext = '{{#invoke: PokePrecSucc | subpage }}\n\n==Artwork==\n{{pokemonimages/head|content=\n'
    pagetext += build_arts(poke, arts, [form[0] for form in forms], gender, artsources, True)
    # concept arts (maybe)
    # concepts = [img for img in imgs if img.startswith('ConceptArt')]
    # if concepts != []:
    #     pagetext += '}}\n\n===Concept art===\n{{pokemonimages/head|content=\n'
    #     for concept in concepts:
    #         pagetext += '{{{{pokemonimages/entry\n|img={}\n|size=x150px\n|downdesc= }}}}\n'.format(concept)
    # main series
    pagetext += '}}\n\n==Sprite e modelli==\n===Serie principale===\n{{pokemonimages/head|content=\n'
    pagetext += build_main(poke, exceptionspath, forms, gender, singleMS, spsc, imgs)
    # spin-offs
    pagetext += '}}\n'
    spinoffimages = get_spinoff_imgs(imgs)
    spinoffstext = build_spinoffs(poke, name, gender, [form[0] for form in forms], spinoffimages, rangerdata, goforms, exceptionspath)
    if spinoffstext:
        pagetext += '\n===Spin-off===\n{{{{pokemonimages/head|content=\n{}}}}}\n'.format(spinoffstext)
    # add category and interwikis
    pagetext += '\n[[Categoria:Sottopagine immagini Pokémon]]\n'
    pagetext += '\n[[de:{}/Sprites und 3D-Modelle]]\n'.format(dename)
    pagetext += '[[fr:{}/Imagerie]]\n'.format(frname)
    # write all wikicode to text file
    with open('{}.txt'.format(os.path.join(pagespath, poke)), 'w') as file:
        file.write(pagetext)
