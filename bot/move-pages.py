import argparse, re, sys, os.path, pywikibot

"""
--fam: family of wiki to use.
--lang: language of wiki to use.
--reason: summary of edits perfomed by the bot.
--noredirect: "true" to move page(s) without leaving redirect behind, "false" otherwise.
--fixlinks: "true" to fix incoming links (see function for details), "false" otherwise.
--file: path of file with list of pages to be moved (is ignored if --old and --new
are provided); should contain title of first page, its new title, title of second
page, new title of second page and so on, one per line (similar to file used by
movepages.py when generator is -pairsfile).
--old: title of page to move (not needed when --file is provided).
--new: new title (same as above).
--test: "false" to perform modifications in wiki, otherwise some info is printed.
"""


# function that fixes links by replacing old title with new title, to ensure that
# templates are fixed along with direct links (the ones in square brackets): old
# title is replaced only if it is a whole word and is not an interwiki
def fix_links(page, replacements, test=True):
    text = ""
    for line in page.text.splitlines():
        if re.search(r"^\[\[\w+:", line):
            text += line + "\n"
        else:
            newline = line
            for replacement in replacements:
                newline = re.sub(replacement[0], replacement[1], newline, flags=re.MULTILINE)  # fmt: skip
            text += newline + "\n"
    if page.text != text:
        page.text = text
        if test:
            print(f"[DEBUG] Fixing links to '{page.title()}'")
            # print(text)
            # break
        else:
            page.save(f"Bot: fixing links to '{page.title()}'")


# function that moves page to new title after performing some checks: new title
# must be different from old one and must not lead to an existing page
def move_page(site, old_title, new_title, reason, noredirect=False, fixlinks=True, test=True):  # fmt: skip
    # get wiki page
    old_page = pywikibot.Page(site, old_title)
    # get links before moving page if needed, to avoid cache issues
    if fixlinks:
        backlinks_titles = [page.title() for page in old_page.backlinks()]
    else:
        backlinks_titles = []
    # check if new title is same as old title
    if old_title == new_title:
        print(f"New title is same as old one: {old_title}")
    else:
        # check that page actually exists
        if not old_page.exists():
            print(f"Cannot find page: {old_title}")
        else:
            # check if new page already exists
            new_page = pywikibot.Page(site, new_title)
            if new_page.exists():
                print(f"Page '{new_title}' already exists, cannot move '{old_title}'")
            else:
                # move page to new title
                print(f"Moving '{old_title}' to '{new_title}'")
                if not test:
                    old_page.move(new_title, reason=reason, noredirect=noredirect)
    return backlinks_titles


# function that moves a file: uses previous function and does not touch links
def move_file(site, old_name, new_name, reason, noredirect=False, test=True):
    # add prefix to titles if necessary
    if not old_name.startswith("File:"):
        old_title = f"File:{old_name}"
    else:
        old_title = old_name
    if not new_name.startswith("File:"):
        new_title = f"File:{new_name}"
    else:
        new_title = new_name
    # move file
    _ = move_page(site, old_title, new_title, reason, noredirect=noredirect, fixlinks=False, test=test)  # fmt: skip


# function to parse a string and return a boolean
def parse_bool(input_string):
    if input_string.strip().lower() == "true":
        return True
    elif input_string.strip().lower() == "false":
        return False
    else:
        sys.exit(f"Failed to parse {input_string}")


# main function
def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--fam", default="encypok")
    parser.add_argument("--lang", default="it")
    parser.add_argument("--reason", default="Bot: moving pages and fixing links")
    parser.add_argument("--noredirect", default="false")
    parser.add_argument("--fixlinks", default="true")
    parser.add_argument("--file", default="")
    parser.add_argument("--old", default="")
    parser.add_argument("--new", default="")
    parser.add_argument("--test", default="true")
    args = parser.parse_args()
    # get site
    site = pywikibot.Site(args.lang, fam=args.fam)
    # check if a single movement was required
    if args.old and args.new:
        movements = [[args.old, args.new]]
    # check if movements are listed in text file
    elif os.path.isfile(args.file):
        with open(args.file, "r") as file:
            lines = file.read().strip().splitlines()
        if len(lines) % 2 == 1:
            sys.exit(f"Invalid file {args.file}")
        else:
            movements = []
            for j in range(len(lines) // 2):
                movements.append([lines[j * 2], lines[j * 2 + 1]])
    else:
        sys.exit("Specify which pages need to be moved!")
    test = parse_bool(args.test)
    noredirect = parse_bool(args.noredirect)
    fixlinks = parse_bool(args.fixlinks)
    backlinks_titles = []
    replacements = []
    for movement in movements:
        old_title = movement[0]
        new_title = movement[1]
        backlinks_page = move_page(site, old_title, new_title, args.reason, noredirect=noredirect, fixlinks=fixlinks, test=test)  # fmt: skip
        backlinks_titles += backlinks_page
        # replacements.append([r"(?<!^\[\[\w\w:)\b{}\b".format(old_title), new_title])
        replacements.append([r"\b{}\b".format(old_title), new_title])
    if backlinks_titles:
        backlinks_fixed = []
        old_titles = [m[0] for m in movements]
        new_titles = [m[1] for m in movements]
        for title in list(set(backlinks_titles)):
            if title not in old_titles:
                backlinks_fixed += [title]
            else:
                backlinks_fixed += [new_titles[old_titles.index(title)]]
        for backlink in backlinks_fixed:
            page = pywikibot.Page(site, backlink)
            fix_links(page, replacements, test=test)


# invoke main function
if __name__ == "__main__":
    main()
