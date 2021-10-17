import pywikibot, re
from datetime import date, timedelta
from subprocess import Popen, PIPE
'''
This script lists pages created during last week (from Monday onwards) in
mainspace; it does not retrieve pages created by bots or redirect removals.
Output is printed to console, listing page title, URL and author.
Exceptions are handled and error messages are printed.
'''
# get last Monday as datetime
today = date.today()
last_monday = today - timedelta(days = today.weekday())
# get list of new pages (intercepts command output)
command = 'python3 pwb.py listpages -format:3 -newpages'
stdout = Popen(command, shell = True, stdout = PIPE).stdout
new_pages = stdout.read().decode().splitlines()
# retrieve pages created last week
site = pywikibot.Site()
last_week_pages = ''
errors = ''
for title in new_pages:
    # handle a possible error (for example if a page was deleted or moved)
    try:
        page = pywikibot.Page(site, title)
        # check date of creation
        creation_time = page.oldest_revision['timestamp']
        creation_date = date.fromisoformat(str(creation_time).split('T')[0])
        if creation_date < last_monday:
            # pages are sorted by creation date, no need to continue
            break
        else:
            author = page.oldest_revision['user']
            # filters to ignore certain pages (in our case the huge amount of cards)
            if re.search(r'(\d+|GCC)\)$', title) and author == 'Andrew01':
                pass
            else:
                last_week_pages += '{} {} ({})\n'.format(title, page.full_url(), author)
    # get error message
    except BaseException as error_message:
        errors += '\n{}\n{}\n'.format(title, error_message)

# print found page(s) and error(s)
if last_week_pages == '':
    print('No pages found!')
else:
    last_week_pages = last_week_pages.strip()
    print('{} pages found:\n\n{}'.format(len(last_week_pages.splitlines()), last_week_pages))
if errors != '':
    print('\nThe following error(s) occurred:\n\n{}'.format(errors.strip()))
