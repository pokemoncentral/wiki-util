#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot removes sections from a page and store the removed text in a local
file.

This bot takes a list of headings as input and removes the sections with a
matching title from a list of pages.

Specific parameters:

-always             Don't prompt for confirmation before editing pages.

-end-of-page        Regex utilized to mark the end of the last section. First
                    line matching.

-end-of-page-regex  Make the end-of-page marker a regular expression.

-heading-regex      Make the headings regular expressions.

-headings-file      File with the list of section headings to be matched. One
                    per line. Will be merged with positional CLI arguments, if
                    given.

-summary:XYZ        Set the summary message text for the edit to XYZ.

-local-file-path    Set the directory for local files that will contain the
                    text removed from pages. The file will be created with the
                    same name as the page edited in the given directory.

other:              Section headings to be matched. Will be merged with the
                    content of -sectionsfile argument, if provided.

These command line parameters can be used to specify which pages to work on:

&pagegenerator-params;
"""

# TODO
# - sections level
# - action
# - language
# - input errors

import codecs
import re
import os
from functools import partial
from itertools import dropwhile

import mwparserfromhell as mwparser
import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot.bot import (
    ExistingPageBot, FollowRedirectPageBot, MultipleSitesBot
)

# This is required for the text that is shown when you run this script with the
# parameter -help.
docuReplacements = {'&pagegenerator-params;': pagegenerators.parameterHelp}


def join_with_last(items, sep=',', last_sep=' and '):
    """Join a sequence using a different separator for the last two items."""
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    return ''.join([sep.join(items[:-1]), last_sep, items[-1]])


class SectionsBot(MultipleSitesBot, ExistingPageBot, FollowRedirectPageBot):
    """A bot that removes sections.

    @param headings: A list used to pick the sections to remove. If it contains
        strings, sections are picked if any of the strings is a substring of
        the section heading. If it contains regexes, a section is picked if the
        heading matches any of the regexes.
    @type headings: list of str
    @param end_of_page_marker: a string/regex used to determine where the last
        section in the page ends: its first match marks the end of the last
        section. When it is a string, it matches if it is a substring of a
        line; when it is a regex, it should itself match.
    @type end_of_page_marker: str
    @param summary: The edit message.
    @type summary: str
    @param local_file_path: The path to a local directory where the file with
        removed sections will be saved
    @type local_file_path: str
    @keyword always: Whether to prompt the user before uploading changes.
    @type always: bool
    """
    def __init__(self, headings, end_of_page_marker=None, summary=None,
                 local_file_path=None, **kwargs):
        """Initializer."""
        super(SectionsBot, self).__init__(**kwargs)

        self.headings = headings
        self.end_of_page_marker = end_of_page_marker
        self.local_file_path = local_file_path
        self.summary = (
            summary
            or 'Bot: removing section{} {}'.format(
                's' if len(headings) > 1 else '',
                join_with_last(headings)
            )
        )

        # Dynamically assigning treat and _match_node methods based on whether
        # end_of_page_marker is passed at all, and whether it is a regex
        if self.end_of_page_marker is not None:
            self.treat = self._treat_end
            self._match_node = (
                re.search
                if isinstance(self.end_of_page_marker, re.Pattern)
                else (lambda eop, n: eop in n)
            )
        else:
            self.treat = self._treat_no_end

        # Dynamically assigning self_match_heading based on whether the section
        # names are regex. Only the first one is checked, as they should be all
        # the same type
        self._match_heading = (
            (lambda from_section, from_user: from_user.search(from_section))
            if isinstance(self.headings[0], re.Pattern)
            else (lambda from_section, from_user: from_user in from_section)
        )

    def _get_end_of_page(self, content):
        """Return the nodes after the end of the first section."""
        return dropwhile(self._is_not_end_of_page, content.nodes)

    def _is_not_end_of_page(self, node):
        """Return whether a node doesn't match the end of page marker."""
        return not self._match_node(self.end_of_page_marker, str(node))

    def _filter_sections(self, heading):
        """Return whether a section heading should be removed."""
        return any(map(partial(self._match_heading, str(heading)),
                       self.headings))

    def _split_end_of_page(self, content):
        """Separate the nodes after the last section from the rest of the page.

        This method removes the nodes after the last section from a page's
        content, and returns the updated content and the removed nodes as a
        list.

        @param content: The content of the page.
        @type content: Wikicode
        """
        end_of_page = list(self._get_end_of_page(content))
        for node in end_of_page:
            content.remove(node)
        return content, end_of_page

    def _treat_end(self, page):
        """Remove matching sections from a page, excluding end of page."""
        # Parsing the page and separating the nodes after the last section.
        content = mwparser.parse(page.text, skip_style_tags=True)
        sections, end_of_page = self._split_end_of_page(content)

        # Removing any section whose titles contain one of the passed headings
        for section in sections.get_sections(matches=self._filter_sections):
            content.remove(section)

        # Readding the nodes after the last section
        for node in end_of_page:
            content.append(node)

        # Uploading the page if necessary
        self.userPut(page=page, oldtext=page.text, newtext=str(content),
                     summary=self.summary)

    def _treat_no_end(self, page):
        """Remove matching sections from a page, including end of page."""
        # Parsing the page.
        content = mwparser.parse(page.text, skip_style_tags=True)

        # Removing any section whose titles contain one of the passed headings
        # and saving it to a local file
        things = mwparser.parse(str(content.get_sections(matches="Mosse apprese")[0]), skip_style_tags=True)
        with open(os.path.join(self.local_file_path, page.title()), "w") as f:
            for section in things.get_sections(matches=self._filter_sections):
                f.write(str(section))
#                content.remove(section)

        # Uploading the page if necessary
#        self.userPut(page=page, oldtext=page.text, newtext=str(content),
#                     summary=self.summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # List of headings, headings file name
    headings, headings_file = [], None
    # Summary message, marker for the beginning of the end of the page (ie
    # the end of the last section), whether to accept all uploads
    summary, end_of_page_marker, always = None, None, False
    # Whether the heading and the end of page markers are regex
    heading_regex, end_of_page_regex = False, False
    # The path to a local directory for storing removed sections in
    local_file_path = None

    genFactory = pagegenerators.GeneratorFactory()

    # Processing all global bot args
    local_args = pwb.handle_args(args)

    # Processing all non-global CLI arguments
    for arg in local_args:
        if genFactory.handleArg(arg):
            continue

        # By convention, all the arguments not starting with - are considered
        # positional.
        if not arg.startswith('-'):
            headings.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(':')

        if arg_name == 'always':
            always = True
        elif arg_name == 'end-of-page':
            end_of_page_marker = arg_value
        elif arg_name == 'end-of-page-regex':
            end_of_page_regex = True
        elif arg_name == 'heading-regex':
            heading_regex = True
        elif arg_name == 'headings-file':
            headings_file = arg_value
        elif arg_name == 'summary':
            summary = arg_value
        elif arg_name == 'local-file-path':
            local_file_path = arg_value

    # Reading the lines of the sections file into headings
    if headings_file:
        with codecs.open(headings_file, 'r', 'utf-8') as f:
            headings.extend(f.read().splitlines())

    # Compiling regex for headings
    if heading_regex:
        headings = list(map(re.compile, headings))

    # Compiling regex for the end-of-page marker
    if end_of_page_regex:
        end_of_page_marker = re.compile(end_of_page_marker)

    bot = SectionsBot(
        always=always,
        end_of_page_marker=end_of_page_marker,
        generator=genFactory.getCombinedGenerator(),
        headings=headings,
        summary=summary,
        local_file_path=local_file_path
    )
    bot.run()

if __name__ == '__main__':
    main()
