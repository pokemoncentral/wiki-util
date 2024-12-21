#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot is designed to moves pages with sequential titles, such as anime episodes.

For example, it has been used to move the XY episodes forwards by one, e.g.
XY078 -> XY079, XY080 -> XY081 ... XY139 -> XY140.

WARNING: Do *NOT* use this bot to move _whatever_ kind of page. Replacing backlinks to
         moved pages is implemented with a naive find-and-replace strategy, which will
         spread chaos with non-sequential page titles.

## Mode of operation

This bot is operated in two steps, with two different commands (as a matter of fact, it
could be two separate bots). This is so that in case anything goes wrong when you
actually operate on the Wiki, you still have the list of pages that should have been
operated on originally. Talking from personal experience, reconstructing the data from
the live Wiki after you have moved and/or updated *some* of the pages can be really
time-consuming.

In the first step you gather the pages to operate on, via the `scan` sub-command. The
result of the search is saved in the file specified in the `-output` argument, in JSON
format. Verify that the content looks plausible before proceeding with the next step!

In the second step you *actually* change stuff on the Wiki, via the `do` sub-command.
The pages to be operated on are input via the `-pages` argument, whose file is in the
same JSON format output by the `scan` sub-command.

## What is carried out

This bot moves sequential pages. It can be used to move a range of pages by a fixed
amount (for instance backwards by two).

Because of this, pages are moved without leaving behind redirects, so the initial page
title can be used by another one in the same range. For example, when moving
EP006 - EP010 backwards by two, we move EP006 -> EP004 and EP008 -> EP006. If EP006 were
moved with redirect, moving EP008 would fail, as EP006 would still exist as a redirect.

Furthermore, pages are moved in ascending or descending order, based on the `-moveorder`
argument. When moving backwards, `-moveorder` should be `ascending`, while when moving
forwards it should be `descending`. This is necessary because we first need to vacate
any existing title before we can move pages. For example, when moving BW037 - BW092
forwards by three, before we can move BW037 -> BW040 we need to move BW040 -> BW043,
BW043 -> BW046, and so on, hence the need to move pages with higher numbers first.

The bot also moves pages whose title contains any of input pages titles, provided that
it links to the initial page. For example, when moving XY122 -> XY123,
"Jimmy (XY122)" -> "Jimmy (XY123)" will also be moved, assuming that it links XY122.
The backlink constraint is enforced to avoid moving unrelated pages that somehow contain
the title of any input page.

Similarly, the bot also moves files whose name contains any of the input page titles,
but only if the file is used in the input page itself, or in any page linking to it.
For instance, when moving XY104 -> XY105, if "File:WTP XY104.png" is used in XY104
then it is moved to "File:WTP XY105.png".
The file-in-use constraint is in place to avoid moving unrelated files that somehow
contain the title of any input page.

Finally, the bot also updates links to the moved pages. This is implemented with a naive
find-and-replace strategy, which only works because sequential pages usually have titles
following some sort of scheme containing numbers and abbreviations. Such titles don't
occur normally in free text or code, making the naive replacement quite safe to execute.
"""
