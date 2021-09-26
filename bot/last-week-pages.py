import pywikibot
from datetime import date, timedelta
from subprocess import Popen, PIPE
'''
This script lists pages created during last week (from Monday onwards) in
mainspace; it does not retrieve pages created by bots or redirect removals.
Output is printed to console, listing page title, URL and author.
'''
site = pywikibot.Site()
# get last Monday as datetime
today = date.today()
last_monday = today - timedelta(days = today.weekday())
# get list of new pages (intercepts command output)
command = 'python3 pwb.py listpages -format:3 -newpages'
stdout = Popen(command, shell = True, stdout = PIPE).stdout
new_pages = stdout.read().decode().splitlines()
# retrieve pages created last week
last_week_pages = ''
for title in new_pages:
    page = pywikibot.Page(site, title)
    # check date of creation
    creation_time = page.oldest_revision['timestamp']
    creation_date = date.fromisoformat(str(creation_time).split('T')[0])
    if creation_date < last_monday:
        # pages are sorted by creation date, no need to continue
        break
    else:
        last_week_pages += '{} {} ({})\n'.format(title, page.full_url(), page.oldest_revision['user'])

print(last_week_pages.strip())
