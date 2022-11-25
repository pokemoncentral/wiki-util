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
'sv': 9,
}

# 'getname' maps ndex to italian name, others map italian name to foreign names
def import_ndex(dexfile):
    getname = {}
    getenname = {}
    getesname = {}
    getdename = {}
    getfrname = {}
    with open(dexfile, 'r') as file:
        for line in file:
            ndex, itname, enname, esname, dename, frname = line.strip().split(',')
            getname.update({ ndex: itname })
            getenname.update({ itname: enname })
            getesname.update({ itname: esname })
            getdename.update({ itname: dename })
            getfrname.update({ itname: frname })
    return getname, getenname, getesname, getdename, getfrname

# import various useful data
def import_data(genderdiffsfile, genderformsfile, femaleonlyfile, artsourcesfile, singlemsfile, availdir, rangerfile, goformsfile):
    with open(genderdiffsfile, 'r') as file:
        genderdiffs = file.read().splitlines()
    with open(genderformsfile, 'r') as file:
        genderforms = file.read().splitlines()
    with open(femaleonlyfile, 'r') as file:
        femaleonly = file.read().splitlines()
    with open(artsourcesfile, 'r') as file:
        artsources = file.read().splitlines()
    availfiles = os.listdir(availdir)
    availdata = {}
    for availfile in availfiles:
        with open(os.path.join(availdir, availfile), 'r') as file:
            availdata.update({ availfile.replace('.csv', ''): file.read().splitlines() })
    with open(singlemsfile, 'r') as file:
        singlemsdata = file.read().splitlines()
    with open(rangerfile, 'r') as file:
        rangerdata = file.read().splitlines()
    with open(goformsfile, 'r') as file:
        goforms = file.read().splitlines()
    return genderdiffs, genderforms, femaleonly, artsources, singlemsdata, availdata, rangerdata, goforms

# get data for given Pokémon
def get_poke_data(poke, genderdiffs, genderforms, femaleonly, singlemsdata):
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
    return gender, singleMS

# get list of alternative forms for given Pokémon
def get_forms(poke, formspath):
    ndex = int(poke)
    last = max(gametogen, key = gametogen.get)
    formsfile = os.path.join(formspath, f'{poke}.csv')
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
        elif ndex <= 905:
            forms = [['', 'lpa', last]]
    return forms

# get all artworks for given form
def insert_arts(pokeabbr, arts, shiny, sources):
    text = ''
    for source in sources:
        # handle these two special cases
        if source == 'PMDDX' and pokeabbr in ['025', '133']:
            text += '|PMDDX=2\n'
            arts.remove(f'Artwork{pokeabbr}m PMDDX.png')
            arts.remove(f'Artwork{pokeabbr}f PMDDX.png')
        else:
            # build name of artwork
            art = f'Artwork{pokeabbr} '
            if shiny == True:
                art += 'cromatico '
            art += f'{source}.png'
            if art in arts:
                # parameter of template pokemonimages/artworks
                sourceabbr = source.replace(' ', '').replace('é', 'e')
                # add found artwork to page and remove it from list of artworks
                # this is needed to retrieve artworks with non-standard name
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
                text += f'|{sourceabbr}={counter}\n'
    return text, arts

# insert piece of template with artworks of given form
# if previous function returns non-empty text, return pokemonimages/artworks
# otherwise nothing is done and empty text is returned
def build_form_arts(pokeabbr, form, arts, sources):
    if len([art for art in arts if f'Artwork{pokeabbr} cromatico' in art]) > 0:
        shinies = True
    else:
        shinies = False
    newtext, arts = insert_arts(pokeabbr, arts, False, sources)
    if newtext:
        text = f'{{{{pokemonimages/artworks\n|ndex={pokeabbr}\n'
        if form == True:
            text += '|form=yes\n'
        if shinies == True:
            text += '|shiny=no\n'
        text += newtext
        if shinies == True:
            if form == True:
                text += f'}}}}\n{{{{pokemonimages/artworks\n|ndex={pokeabbr}\n|form=yes\n|shiny=yes\n'
            else:
                text += f'}}}}\n{{{{pokemonimages/artworks\n|ndex={pokeabbr}\n|shiny=yes\n'
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
        text = text.replace('|form=yes', '|gender=m\n|bothgenders=yes', 1)
        text = text.replace('|form=yes', '|gender=f\n|bothgenders=yes', 1)
    # unused arts (those with non-standard names)
    if extras == True and arts != []:
        text += '\n{{pokemonimages/div|text=Altri}}\n'
        for art in arts:
            text += f'{{{{pokemonimages/entry\n|xl=20|md=25|sm=33|xs=50\n|img={art}\n|size=x150px\n|downdesc= (artwork da [[]]) }}}}\n'
    return text

# check if given Pokémon/form is available in given game
def check_pokeform_game_availability(poke, form, game, availdata):
    abbr, since, until = form
    game_gen = gametogen[game]
    if int(game_gen) >= 8:
        game_pokes = availdata[game]
        # if base form, simply check if ndex is in list
        if abbr == '':
            if poke in game_pokes:
                is_available = True
            else:
                is_available = False
        # with alt forms, additional checks are required
        else:
            pokeabbr = poke + abbr
            # if game contains alt form(s) of a Pokémon but not base form, list will
            # contain all alt forms instead of base form
            if pokeabbr in game_pokes:
                is_available = True
            # if list doesn't contain base form, alt form is not available in game
            elif poke not in game_pokes:
                is_available = False
            # game contains base form, check if alt form is available
            else:
                is_available = (gametogen[since] <= game_gen and gametogen[until] >= game_gen)
    else:
        is_available = (gametogen[since] <= game_gen and gametogen[until] >= game_gen)
    return is_available

# get all games in given generation where given form is available
def get_pokeform_gen_games(poke, form, gen, availdata):
    gen_games = [game for game in gametogen if int(gametogen[game]) == int(gen)]
    return [game for game in gen_games if check_pokeform_game_availability(poke, form, game, availdata)]

# build a single pokemonimages/main* for a single form
def build_main_gen_entry(poke, form, gen, availdata, isform = False, since = '', female = False, bothgenders = False, gen4common = ''):
    text = ''
    if isform:
        text += '|form=yes'
    if since:
        text += f'|since={since}'
    if female:
        text += '|gender=f'
    if bothgenders:
        text += '|bothgenders=yes'
    # some Pokémon have same sprites in DPPt or PtHGSS or all games
    if gen == '4' and gen4common:
        text += f'|{gen4common}=yes'
    # add abbrs of single games (used from generation VIII onwards because games
    # no longer contain all previous Pokémon)
    if int(gen) >= 8:
        games = get_pokeform_gen_games(poke, form, gen, availdata)
        if games:
            for game in games:
                text += f'|{game}=yes'
        else:
            text = None
    # if there are no entries return empty string
    if text is not None:
        text = f'{{{{pokemonimages/main{gen}|ndex={poke}{form[0]}{text}}}}}'
    else:
        text = ''
    return text

# build all pokemonimages/main* entries for given Pokémon in given generation
def build_main_gen(poke, gen, availdata = {}, forms = [], gender = '', gen4sprites = []):
    text = ''
    # search for other forms that esist in given generation
    numgen = int(gen)
    if len([form for form in forms if get_pokeform_gen_games(poke, form, gen, availdata)]) > 1:
        multiform = True
    else:
        multiform = False
    # gender forms
    if [form[0] for form in forms[:2]] == ['', 'F'] and gender in ['both', 'bothforms']:
        # gender difference is treated as useless form
        if gender == 'both':
            text += f'{build_main_gen_entry(poke, forms[0], gen, availdata, isform = False, bothgenders = True)}\n'
            text += f'{build_main_gen_entry(poke, forms[0], gen, availdata, isform = False, female = True, bothgenders = True)}\n'
        # gender difference is treated as alt form
        else:
            text += f'{build_main_gen_entry(poke, forms[0], gen, availdata, isform = True)}\n'
            text += f'{build_main_gen_entry(poke, forms[0], gen, availdata, isform = True, female = True)}\n'
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
                if f'Sprdpm{pokeabbr}.png' in gen4sprites or f'Sprdpf{pokeabbr}.png' in gen4sprites:
                    gen4 += 'dp'
                if f'Sprptm{pokeabbr}.png' in gen4sprites or f'Sprptf{pokeabbr}.png' in gen4sprites:
                    gen4 += 'pt'
                if f'Sprhgssm{pokeabbr}.png' in gen4sprites or f'Sprhgssf{pokeabbr}.png' in gen4sprites:
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
        middlegen = (numgen < gametogen[since] and numgen == int(gametogen[since]))
        # maybe the following part can be done better, but it works and I don't want to break it
        if abbr == '':
            # gender differences
            if gender == 'both':
                text += f'{build_main_gen_entry(poke, form, gen, availdata, isform = False, bothgenders = True, gen4common = gen4common)}\n'
                text += f'{build_main_gen_entry(poke, form, gen, availdata, isform = False, female = True, bothgenders = True, gen4common = gen4common)}\n'
            # female only
            elif gender == 'f':
                text += f'{build_main_gen_entry(poke, form, gen, availdata, isform = multiform, female = True, gen4common = gen4common)}\n'
            # other cases
            else:
                # check if was introduced in the middle of the generation
                if numgen >= 8 or not middlegen:
                    since = ''
                text += f'{build_main_gen_entry(poke, form, gen, availdata, isform = multiform, since = since, female = False, gen4common = gen4common)}\n'
        elif abbr == 'F' and gender == 'both':
            pass # already done
        elif floor(gametogen[since]) <= numgen and numgen <= gametogen[until]:
            if gender == 'f':
                female = True
            else:
                female = False
            # check if was introduced in the middle of the generation
            if numgen >= 8 or not middlegen:
                since = ''
            text += f'{build_main_gen_entry(poke, form, gen, availdata, isform = True, since = since, female = female, gen4common = gen4common)}\n'
    # if there are no entries for this gen return empty string
    if text.strip():
        text = f'{{{{pokemonimages/group|gen={gen}|content=\n{text}}}}}\n'
    else:
        text = ''
    return text

# build mini sprites entry for given form
def build_ms_entry(poke, form, multiform, availdata, gender, genderform = ''):
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
        text = f'{{{{pokemonimages/mainMS|ndex={pokeabbr}'
        if genderform:
            text += f'|bothgenders=yes|gender={genderform}'
        if start <= 1:
            text += '|ms1=yes'
        if start <= 2:
            text += '|ms2=yes'
        if floor(start) <= 5:
            text += f'|ms345={ms345.get(start, "345")}'
        if floor(start) <= 7 and end >= 6:
            if end < 7:
                text += '|ms67=rozaonly'
            else:
                text += f'|ms67={ms67.get(start, "67")}'
        if check_pokeform_game_availability(poke, form, 'spsc', availdata):
            text += '|msspsc=yes'
        if check_pokeform_game_availability(poke, form, 'dlps', availdata):
            text += '|msdlps=yes'
        # some ndexes are hardcoded here, because game won't change and it's
        # much easier than reading this info from external file
        if check_pokeform_game_availability(poke, form, 'lpa', availdata):
            if gender == 'both':
                text += '|mslpa=both'
            elif gender == 'f':
                text += '|mslpa=female'
            elif pokeabbr in ['059H', '101H', '713H', '900']:
                text += '|mslpa=rm'
            elif pokeabbr == '549H':
                text += '|mslpa=rf'
            else:
                text += '|mslpa=single'
        if multiform == True:
            text += '|form=yes'
            # these forms don't have an overworld sprite in HGSS
            if pokeabbr in ['351S', '351P', '351N', '421S']:
                text += '|overworld=no'
        text += '}}\n'
    return text

# build main series entries
def build_main(poke, exceptionspath, forms, gender, singleMS, availdata, imgs):
    text = ''
    # check for exception
    exceptionfile = os.path.join(exceptionspath, f'{poke}_main.txt')
    if os.path.isfile(exceptionfile):
        with open(exceptionfile, 'r') as file:
            text += file.read()
    else:
        ndex = int(poke)
        if ndex <= 151:
            text += build_main_gen(poke, '1', forms = forms)
        if ndex <= 251:
            text += build_main_gen(poke, '2', forms = forms)
        if ndex <= 385:
            text += build_main_gen(poke, '3', forms = forms)
        if ndex == 386:
            with open(os.path.join(exceptionspath, f'{poke}_main3.txt'), 'r') as file:
                text += file.read().strip()
        if ndex <= 493:
            gen4sprites = [img for img in imgs if re.search(r'^Spr(dp|pt|hgss)', img)]
            text += build_main_gen(poke, '4', forms = forms, gender = gender, gen4sprites = gen4sprites)
        if ndex <= 649:
            text += build_main_gen(poke, '5', forms = forms, gender = gender)
        if ndex <= 721:
            text += build_main_gen(poke, '6', forms = forms, gender = gender)
        if ndex <= 807:
            text += build_main_gen(poke, '7', forms = forms, gender = gender)
        if ndex <= 905:
            text += build_main_gen(poke, '8', availdata = availdata, forms = forms, gender = gender)
        # mini sprites
        text += '{{pokemonimages/group|gen=MS|content=\n'
        # check for exception
        exceptionfile = os.path.join(exceptionspath, f'{poke}_mainMS.txt')
        if os.path.isfile(exceptionfile):
            with open(exceptionfile, 'r') as file:
                text += file.read()
        else:
            if singleMS == True:
                text += build_ms_entry(poke, forms[0], False, availdata, gender)
            else:
                if len(forms) > 1:
                    multiform = True
                else:
                    multiform = False
                if [form[0] for form in forms[:2]] == ['', 'F'] and gender == 'both':
                    text += build_ms_entry(poke, forms[0], False, availdata, gender, genderform = 'm')
                    text += build_ms_entry(poke, forms[1], False, availdata, gender, genderform = 'f')
                    if len(forms) > 2:
                        for form in forms[2:]:
                            text += build_ms_entry(poke, form, multiform, availdata, gender)
                else:
                    for form in forms:
                        text += build_ms_entry(poke, form, multiform, availdata, gender)
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
        if f'Sprstad{pokeabbr}.png' in imgs:
            formtext += '|stadium=StS2\n'
        elif f'Sprstad2{pokeabbr}.png' in imgs:
            formtext += '|stadium=S2\n'
        if abbr == '':
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
            if name not in ['Pikachu', 'Clefairy', 'Jynx']:
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
            if f'Pin{pokeabbr}.png' in imgs:
                pinball += 'rb'
            if f'PinRZ{pokeabbr}.png' in imgs:
                pinball += 'rz'
            if f'Pinani{pokeabbr}.gif' in imgs or f'PinRZani{pokeabbr}.gif' in imgs:
                pinball += 'double'
            else:
                pinball += 'single'
            if pinball.replace('single', ''):
                formtext += f'|pinball={pinball}\n'
            # Puzzle Challenge
            if f'PuzzleChallenge{pokeabbr}.png' in imgs:
                formtext += '|puzzlechallenge=yes\n'
        # Auros
        if f'Sprcolo{pokeabbr}.png' in imgs:
            formtext += '|auros=coloxd\n'
        elif f'Sprxdsh{pokeabbr}.png' in imgs:
            formtext += '|auros=xd\n'
        elif f'Sprxd{pokeabbr}.png' in imgs:
            formtext += '|auros=xdsingle\n'
        # Dash
        if f'Dash{pokeabbr}.png' in imgs:
            formtext += '|dash=yes\n'
        # Link
        if f'Linkani{pokeabbr}.gif' in imgs and f'LB{pokeabbr}.png' in imgs:
            formtext += '|link=both\n'
        elif f'Linkani{pokeabbr}.gif' in imgs:
            formtext += '|link=link\n'
        elif f'LB{pokeabbr}.png' in imgs:
            formtext += '|link=battle\n'
        # Team Turbo
        if f'TeamTurbo{pokeabbr}.png' in imgs:
            formtext += '|teamturbo=yes\n'
        # Mystery Dungeon
        if f'MDSprrb{pokeabbr}.png' in imgs:
            formtext += '|mdrbtoc=rbtoc\n'
        elif f'MDSprtoc{pokeabbr}.png' in imgs:
            if pokeabbr in ['487O', '492', '492C']:
                formtext += '|mdrbtoc=c\n'
            else:
                formtext += '|mdrbtoc=toc\n'
        if f'MDPPSI{pokeabbr}.png' in imgs:
            formtext += '|mdpsi=yes\n'
        if f'MDPSuper{pokeabbr} sh.png' in imgs:
            formtext += '|mdsuper=shiny\n'
        elif f'MDPSuper{pokeabbr} f.png' in imgs:
            formtext += '|mdsuper=both\n'
        elif f'MDPSuper{pokeabbr}.png' in imgs:
            formtext += '|mdsuper=normal\n'
        mddx = ''
        if f'MDPDX{pokeabbr}.png' in imgs:
            mddx += 'mn'
        if f'MDPDX{pokeabbr} f.png' in imgs:
            mddx += 'fn'
        if f'MDPDXsh{pokeabbr}.png' in imgs:
            mddx += 'msh'
        if f'MDPDXsh{pokeabbr} f.png' in imgs:
            mddx += 'fsh'
        if mddx:
            formtext += f'|mddx={mddx}\n'
        mddxmini = ''
        if f'MDSprdx{pokeabbr}.png' in imgs:
            mddxmini += 'mn'
        if f'MDSprdx{pokeabbr} f.png' in imgs:
            mddxmini += 'fn'
        if f'MDSprdx{pokeabbr} sh.png' in imgs:
            mddxmini += 'msh'
        if f'MDSprdx{pokeabbr} f sh.png' in imgs:
            mddxmini += 'fsh'
        if mddxmini:
            formtext += f'|mddxmini={mddxmini}\n'
        # Ranger
        ranger1 = f'Sprranger{pokeabbr}.png'
        ranger2 = f'Sprrangerosa{pokeabbr}.png'
        ranger3 = f'Sprrangertdl{pokeabbr}.png'
        if ranger1 in imgs:
            ranger = 'ranger1'
            if f'{ranger2} > {ranger1}' in rangerdata:
                ranger += '2'
            if f'{ranger3} > {ranger1}' in rangerdata:
                ranger += '3'
            formtext += f'|{ranger}=yes\n'
        if ranger2 in imgs:
            ranger = 'ranger2'
            if f'{ranger3} > {ranger2}' in rangerdata:
                ranger += '3'
            formtext += f'|{ranger}=yes\n'
        if ranger3 in imgs:
            formtext += '|ranger3=yes\n'
        if re.search(r'(\|ranger\d\d=yes\n\|ranger\d=yes|\|ranger\d=yes\n\|ranger\d\d=yes)', formtext):
            print(pokeabbr)
        # Battle Revolution
        if f'PBR{pokeabbr}.png' in imgs:
            formtext += '|pbr=single\n'
        elif f'PBR{pokeabbr}m.png' in imgs and f'PBR{pokeabbr}f.png' in imgs:
            formtext += '|pbr=both\n'
        # Rumble
        rumble = ''
        if f'SPR{pokeabbr}.png' in imgs:
            rumble += '2'
        if f'PRW{pokeabbr}.png' in imgs:
            rumble += '4'
        if f'Rush{pokeabbr} f.png' in imgs:
            rumble += '5g'
        elif f'Rush{pokeabbr}.png' in imgs:
            rumble += '5'
        if rumble:
            formtext += f'|rumble={rumble}\n'
        # PokéPark
        if f'PPWM{pokeabbr}.png' in imgs:
            formtext += '|pokepark=both\n'
        elif f'PPW{pokeabbr}.png' in imgs or f'PP2{pokeabbr}.png' in imgs:
            formtext += '|pokepark=sprite\n'
        # Dream World
        if f'PDW{pokeabbr}.png' in imgs:
            formtext += '|pdw=yes\n'
        # Impara con Pokémon
        if f'ICP{pokeabbr}.png' in imgs:
            formtext += '|icp=yes\n'
        # Conquest
        if f'PCP{pokeabbr}.png' in imgs:
            formtext += '|cq=yes\n'
        # Pokédex 3D Pro
        if f'P3P{pokeabbr}.png' in imgs:
            formtext += '|p3p=yes\n'
        # Shuffle
        if f'Shuffle{pokeabbr}.png' in imgs:
            formtext += '|shuffle=yes\n'
            if f'Shuffle{pokeabbr}cr.png' in imgs:
                formtext += '|shufflecr=yes\n'
            if f'Shuffle{pokeabbr}oc.png' in imgs:
                formtext += '|shuffleoc=yes\n'
            if f'Shuffle{pokeabbr}im.png' in imgs:
                formtext += '|shuffleim=yes\n'
            if f'Shuffle{pokeabbr}fe.png' in imgs:
                formtext += '|shufflefe=yes\n'
            if f'Shuffle{pokeabbr}boss.png' in imgs:
                formtext += '|shuffleboss=yes\n'
        # Super Mario maker
        if f'SMM{pokeabbr}.png' in imgs:
            formtext += '|smm=yes\n'
        # Picross
        if f'Picross{pokeabbr}.png' in imgs:
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
        if f'GO{pokeabbr} f s.png' in imgs:
            formtext += '|go=shinyboth\n'
        elif f'GO{pokeabbr} s.png' in imgs:
            formtext += '|go=shiny\n'
        elif f'GO{pokeabbr} f.png' in imgs:
            formtext += '|go=both\n'
        elif f'GO{pokeabbr}.png' in imgs:
            formtext += '|go=normal\n'
        # Magikarp Jump
        if f'MJ{pokeabbr}.png' in imgs:
            formtext += '|mj=yes\n'
        # Casetta dei Pokémon
        if f'CDP{pokeabbr}.png' in imgs:
            formtext += '|cdp=yes\n'
        # Detective Pikachu
        if f'DetectivePikachu{pokeabbr}.png' in imgs:
            formtext += '|dp=yes\n'
        # Quest
        if f'QuestSpr{pokeabbr}.png' in imgs:
            formtext += '|quest=yes\n'
        # Masters
        if f'MastersEX{pokeabbr}f.png' in imgs:
            formtext += '|mastersnormal=both\n'
        elif f'MastersEX{pokeabbr}.png' in imgs:
            formtext += '|mastersnormal=single\n'
        if f'MastersEXsh{pokeabbr}f.png' in imgs:
            formtext += '|mastersshiny=both\n'
        elif f'MastersEXsh{pokeabbr}.png' in imgs:
            formtext += '|mastersshiny=single\n'
        if f'MastersIcona{pokeabbr} f.png' in imgs:
            formtext += '|mastersmugshot=both\n'
        elif f'MastersIcona{pokeabbr}.png' in imgs:
            formtext += '|mastersmugshot=single\n'
        # HOME
        # gender differences treated as useless forms need some fixes
        if uselessgender == True and abbr in ['', 'F']:
            if abbr == '':
                if f'Homemsh{poke}.png' in imgs:
                    formtext += '|home=shiny\n'
                elif f'Homem{poke}.png' in imgs:
                    formtext += '|home=normal\n'
            else:
                if f'Homemsh{poke}.png' in imgs:
                    formtext += '|home=shinyfemale\n'
                elif f'Homem{poke}.png' in imgs:
                    formtext += '|home=normalfemale\n'
        else:
            if f'Homemsh{pokeabbr}.png' in imgs and f'Homefsh{pokeabbr}.png' in imgs:
                formtext += '|home=shinyboth\n'
            elif f'Homefsh{pokeabbr}.png' in imgs:
                formtext += '|home=shinyfemale\n'
            elif f'Homemsh{pokeabbr}.png' in imgs:
                formtext += '|home=shiny\n'
            elif f'Homem{pokeabbr}.png' in imgs and f'Homef{pokeabbr}.png' in imgs:
                formtext += '|home=normalboth\n'
            elif f'Homef{pokeabbr}.png' in imgs:
                formtext += '|home=normalfemale\n'
            elif f'Homem{pokeabbr}.png' in imgs:
                formtext += '|home=normal\n'
        # Smile
        if f'Smile{pokeabbr}.png' in imgs:
            formtext += '|smile=yes\n'
        if f'SmileCostume{pokeabbr} 4.png' in imgs:
            formtext += '|smilecostume=4\n'
        elif f'SmileCostume{pokeabbr} 2.png' in imgs:
            formtext += '|smilecostume=2\n'
        if f'SmileIcona{pokeabbr}.png' in imgs:
            formtext += '|smileicona=yes\n'
        if f'SmileDormiente{pokeabbr}.png' in imgs:
            formtext += '|smiledormiente=yes\n'
        if f'SmileConsiglio{pokeabbr}.png' in imgs:
            formtext += '|smileconsiglio=yes\n'
        if pokeabbr in ['007', '025', '133']:
            extra = [img for img in imgs if re.search(r'Smile(.*){}'.format(name), img)]
            counter = 0
            for img in extra:
                counter += 1
                formtext += '|smileextra{}={}\n'.format(str(counter).replace('1', ''), re.sub(r'SmileCostume (.+)\.png', r'\1', img))
        # Café ReMix
        cafemix = ''
        if f'CafeMixSprite{pokeabbr} staff.png' in imgs:
            cafemix += 's'
        if f'CafeMixSprite{pokeabbr} guest.png' in imgs:
            cafemix += 'g'
        if f'CafeMixSprite{pokeabbr} tassello.png' in imgs:
            cafemix += 't'
        if cafemix:
            formtext += f'|cafemix={cafemix}\n'
        # New Pokémon Snap
        if f'NPS{pokeabbr}.png' in imgs:
            formtext += '|newsnap=yes\n'
        # add only if there are entries for this form
        if formtext:
            texts.append([pokeabbr, formtext])
    if len(texts) > 1:
        for text in texts:
            finaltext += f'{{{{pokemonimages/spinoff\n|ndex={text[0]}\n|form=yes\n{text[1]}}}}}\n'
        # fix gender differences treated as useless forms
        if uselessgender == True:
            finaltext = finaltext.replace('|form=yes', '|gender=m\n|bothgenders=yes', 1)
            finaltext = finaltext.replace('|form=yes', '|gender=f\n|bothgenders=yes', 1)
    elif len(texts) == 1:
        finaltext = f'{{{{pokemonimages/spinoff\n|ndex={texts[0][0]}\n{texts[0][1]}}}}}\n'
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
        if f'GO{poke} {goform}.png' in imgs:
            if f'GO{poke} {goform} f.png' in imgs:
                if f'GO{poke} {goform} s.png' in imgs:
                    text = 'shinyboth'
                else:
                    text = 'both'
            else:
                if f'GO{poke} {goform} s.png' in imgs:
                    text = 'shiny'
                else:
                    text = 'normal'
            extrago += f'|{goform.lower()}={text}\n'
    if extrago:
        finaltext += f'{{{{pokemonimages/extraGO\n|ndex={poke}\n{extrago}}}}}\n'
    # MDDX extras
    search = r'MDPDX{}\-(\w+)\.png'.format(poke)
    extramddx = [img for img in imgs if re.search(search, img)]
    if len(extramddx) > 0:
        extras = [re.sub(search, r'\1', img) for img in extramddx]
        finaltext += '{{{{pokemonimages/extraMDDX|ndex={}|{}}}}}\n'.format(poke, '|'.join(extras))
    # Café Mix extras
    cmfile = os.path.join(exceptionspath, f'{poke}_extraCM.txt')
    if os.path.isfile(cmfile):
        with open(cmfile, 'r') as file:
            finaltext += file.read()
    return finaltext

# build wikicode of page for given Pokémon
def build_poke_page(poke, name, pokelistspath, pagespath, formspath, artsources, goforms, exceptionspath, gender, singleMS, availdata, rangerdata, enname, esname, dename, frname):
    # get alternative forms
    forms = get_forms(poke, formspath)
    # get list of images of given Pokémon
    with open(f'{os.path.join(pokelistspath, poke)}.txt', 'r') as pokefile:
        imgs = pokefile.read().splitlines()
    # artworks
    arts = [img for img in imgs if img.startswith('Artwork')]
    pagetext = '{{#invoke: PokePrecSucc | subpage }}\n\n==Artwork==\n{{pokemonimages/head|content=\n'
    pagetext += build_arts(poke, arts, [form[0] for form in forms], gender, artsources, True)
    # main series
    pagetext += '}}\n\n==Sprite e modelli==\n===Serie principale===\n{{pokemonimages/head|content=\n'
    pagetext += build_main(poke, exceptionspath, forms, gender, singleMS, availdata, imgs)
    # spin-offs
    pagetext += '}}\n'
    spinoffimages = get_spinoff_imgs(imgs)
    spinoffstext = build_spinoffs(poke, name, gender, [form[0] for form in forms], spinoffimages, rangerdata, goforms, exceptionspath)
    if spinoffstext:
        pagetext += f'\n===Spin-off===\n{{{{pokemonimages/head|content=\n{spinoffstext}}}}}\n'
    # add category and interwikis
    pagetext += '\n[[Categoria:Sottopagine immagini Pokémon]]\n\n'
    pagetext += f'[[de:{dename}/Sprites und 3D-Modelle]]\n'
    #pagetext += f'[[en:Category:{enname}]]\n'
    #pagetext += f'[[es:{esname}/...]]\n'
    pagetext += f'[[fr:{frname}/Imagerie]]\n'
    # write all wikicode to text file
    with open(f'{os.path.join(pagespath, poke)}.txt', 'w') as file:
        file.write(pagetext)
