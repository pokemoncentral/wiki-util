import re
import pywikibot
from pywikibot import pagegenerators

site = pywikibot.Site()
cat = pywikibot.Category(site, 'Categoria:Pokémon di ottava generazione')
listofpages = pagegenerators.CategorizedPageGenerator(cat)

# Value to insert if data is not found in the page
# Since only EVs yield are present, others are 0
datanotfound = {
    'evhp': '0',
    'evat': '0',
    'evde': '0',
    'evsa': '0',
    'evsd': '0',
    'evsp': '0',
    'espceduta': '?',
}

# param is the name of the parameter
# text is usually the entire page
def finddata(param, text):
    search = param + '=(.*?)(\||\n)'
    regex = re.compile(search)
    match = regex.search(text)
    if match:
        res = match.group(1).strip()
        if res == '':
            res = datanotfound.get(param, '')
    else:
        res = datanotfound.get(param, '')
    return res

# Get data from page and rearrange it to use lop/ev template
def findevs(pagetext):
    parts = ['{{lop/ev']
    parts.append(finddata('ndex', pagetext))
    parts.append(finddata('nome', pagetext))
    parts.append(finddata('espceduta', pagetext))
    parts.append(finddata('evhp', pagetext))
    parts.append(finddata('evat', pagetext))
    parts.append(finddata('evde', pagetext))
    parts.append(finddata('evsa', pagetext))
    parts.append(finddata('evsd', pagetext))
    parts.append(finddata('evsp', pagetext))
    line = '|'.join(parts) + '}}'
    lines.append(line)

# clears file content and prepares the list of lines
open('evs8', 'w').close()
lines = []
'''
teststring = 'nome=Morpeko |ndex=890|altrecose'
findevs(teststring)

page = pywikibot.Page(site, u'Alcremie')
findevs(page.text)
'''
for page in listofpages:
    findevs(page.text)

lines.sort()
for line in lines:
    with open('evs8', 'a') as outfile:
        outfile.write(line + '\n')
