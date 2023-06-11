"""
This script lists pages created during last week (from Monday onwards) in
mainspace; it does not retrieve pages created by bots or redirect removals.
Output is printed to console, listing page title, URL and author.
Exceptions are handled and error messages are printed.

Options:

-late       If given, returns pages of the previous week, not the current one
"""

import sys
import re
import pywikibot
import pywikibot.pagegenerators
from datetime import date, timedelta


def should_exclude(page):
    """Whether the page should be excluded from the list."""
    cats = [cat.title() for cat in page.categories()]
    # cards
    if page.title().endswith("(GCC)") or "Categoria:Carte Pokémon" in cats:
        return True
    # disambiguations
    if "Categoria:Pagine di disambiguazione" in cats:
        return True
    return False


# get today and last Monday
today = date.today()
last_monday = today - timedelta(days=today.weekday())
if "-late" in sys.argv:
    # get previous week
    start_date = last_monday - timedelta(days=7)
    end_date = last_monday - timedelta(days=1)
else:
    # get current week
    start_date = last_monday
    end_date = today

# retrieve pages created last week
last_week_pages = []
errors = []
for page in pywikibot.pagegenerators.NewpagesPageGenerator(pywikibot.Site()):
    # handle a possible error (for example if a page was deleted or moved)
    try:
        # check date of creation
        creation_time = page.oldest_revision["timestamp"]
        creation_date = date.fromisoformat(str(creation_time).split("T")[0])
        if creation_date < start_date:
            # pages are sorted by creation date, no need to continue
            break
        elif creation_date > end_date:
            # ignore pages created after end date (needed with -late)
            pass
        else:
            # filters to ignore certain pages
            if not should_exclude(page):
                author = page.oldest_revision["user"]
                last_week_pages.append(
                    "{} {} ({})".format(page.title(), page.full_url(), author)
                )
    # get error message
    except Exception as error_message:
        errors.append(str(error_message))

# print found page(s) and error(s)
if last_week_pages:
    print(
        "{} pages found:\n\n{}".format(len(last_week_pages), "\n".join(last_week_pages))
    )
else:
    print("No pages found!")
if errors:
    print("\n\n#### The following error(s) occurred:\n" + "\n".join(errors))
