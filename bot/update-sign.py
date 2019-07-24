import re
import pywikibot
from pywikibot import pagegenerators

site = pywikibot.Site()
cat = pywikibot.Category(site, 'Categoria:Zone Unima')
listofpages = pagegenerators.CategorizedPageGenerator(cat)

first_param_mapping = {
    'nbbuilding': 'generico',
    'BWbuilding': 'generico',
    'nb': 'slogan città',
    'BW': 'slogan città',
    'nbtip': 'consigli utili',
    'BWtip': 'consigli utili',
}

first_params = '|'.join(first_param_mapping.keys())
is_sign = re.compile(r'\{\{[Ss]ign\|')
grep_header = re.compile(r'\{\{[Ss]ign\|(%s)\|header\}\}' % first_params)
grep_footer = re.compile(r'\{\{[Ss]ign\|(%s)\|footer\}\}' % first_params)
grep_title = re.compile(r'\{\{[Ss]ign\|(%s)\|title\|(.*?)\}\}' % first_params)
grep_content = re.compile(r'\{\{[Ss]ign\|(%s)\|(.*?)\}\}' % first_params)

def FixSign(pagetext):
    lines = []
    count = 0

    for line in pagetext.splitlines():
        if is_sign.search(line):

            # Footer
            line = grep_footer.sub('}}', line)

            # Header
            header, subs = grep_ha

            header = grep_header.match(line)
            if header:
                count = 0
                replacement = ('{{sign/5|%s'
                               % first_param_mapping[header.group(1)])
                line = grep_header.sub(replacement, line)

            # Title
            title = grep_title.match(line)
            if title:
                count += 1
                replacement = "|r{}='''{}'''".format(count, title.group(2))
                line = grep_title.sub(replacement, line)

            # Content
            content = grep_content.match(line)
            if content:
                count += 1
                replacement = "|r{}={}".format(count, content.group(2))
                line = grep_content.sub(replacement, line)

        lines.append(line)

    return '\n'.join(lines)

page = pywikibot.Page(site, u'Utente:Lucas992/Sandbox')
page.text = FixSign(page.text)
page.save(u'Test Sign')
'''
for page in listofpages:
    #print(page.title)
    if is_sign.search(page.text):
        page.text = FixSign(page.text)
        page.save(u'Bot: fixing Sign usage for Unima locations')
'''
