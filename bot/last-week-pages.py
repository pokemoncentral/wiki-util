import pywikibot, re
import pywikibot.pagegenerators
from datetime import date, timedelta
'''
This script lists pages created during last week (from Monday onwards) in
mainspace; it does not retrieve pages created by bots or redirect removals.
Output is printed to console, listing page title, URL and author.
Exceptions are handled and error messages are printed.
'''
# get last Monday as datetime
today = date.today()
last_monday = today - timedelta(days = today.weekday())

# retrieve pages created last week
last_week_pages = []
errors = []
for page in pywikibot.pagegenerators.NewpagesPageGenerator(pywikibot.Site()):
    # handle a possible error (for example if a page was deleted or moved)
    try:
        # check date of creation
        creation_time = page.oldest_revision['timestamp']
        creation_date = date.fromisoformat(str(creation_time).split('T')[0])
        if creation_date < last_monday:
            # pages are sorted by creation date, no need to continue
            break
        else:
            title = page.title()
            author = page.oldest_revision['user']
            # filters to ignore certain pages
            # we are ignoring cards and disambiguation pages
            if re.search(r'(\d+|GCC)\)$', title) and author == 'Andrew01':
                pass
            elif 'Categoria:Pagine di disambiguazione' in [cat.title() for cat in page.categories()]:
                pass
            else:
                last_week_pages.append('{} {} ({})'.format(title, page.full_url(), author))
    # get error message
    except Exception as error_message:
        errors.append(str(error_message))

# print found page(s) and error(s)
if last_week_pages:
    print('{} pages found:\n\n{}'.format(len(last_week_pages), "\n".join(last_week_pages)))
else:
    print('No pages found!')
if errors:
    print('\n\n#### The following error(s) occurred:\n' + '\n'.join(errors))
