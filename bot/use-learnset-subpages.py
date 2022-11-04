#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
Look for section "Mosse apprese" in the given page, removes most of its
subsections (ideally just GCC- and anime-only subsections should survive
the onslaught) and replaces them with an inclusion of the appropriate
subpage.

These command line parameters can be used to specify which pages to work on:

&pagegenerator-params;
"""

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


class MosseAppreseBot(MultipleSitesBot, ExistingPageBot, FollowRedirectPageBot):
    SECTIONS = (
        "Aumentando di \[\[livello\]\]",
        "Tramite \[\[MT\]\]/\[\[DT\]\]",
        "Tramite \[\[MT\]\]",
        "Tramite \[\[MT\]\]/\[\[MN\]\]",
        "Tramite \[\[Accoppiamento Pokémon\|accoppiamento\]\]",
        "Dall'\[\[Insegnamosse\]\]",
        "Tramite \[\[evoluzione\|evoluzioni\]\] precedenti"
    )

    SUBPAGE_INC_REGEX = "{{/Mosse apprese in [\w]+ generazione}}"
    SUBPAGE_INCLUSION = "\n{{/Mosse apprese in settima generazione}}\n"

    """A bot that removes sections.

    @param summary: The edit message.
    @type summary: str
    @keyword always: Whether to prompt the user before uploading changes.
    @type always: bool
    """
    def __init__(self, summary=None, **kwargs):
        """Initializer."""
        super(MosseAppreseBot, self).__init__(**kwargs)

        self.summary = (
            summary
            or 'Bot: replacing "Mosse apprese" with subpage inclusion'
        )

    def treat(self, page):
        # Parsing the page
        content = mwparser.parse(page.text, skip_style_tags=True)

        # Look for section "Mosse apprese"
        try:
            limited_content = content.get_sections(matches="Mosse apprese")[0]
        except IndexError:
            pwb.error("Can't find section \"Mosse apprese\" in page {}".format(page.title))
            raise ValueError()
        # Check if the section already contains a subpage inclusion
        if limited_content.filter_templates(matches=MosseAppreseBot.SUBPAGE_INC_REGEX):
            pwb.output("Page {} already includes subpage for Mosse apprese".format(page.title()))
            return

        for heading in MosseAppreseBot.SECTIONS:
            for section in limited_content.get_sections(matches=heading):
                content.remove(section)

        # Add subpage inclusion right after the heading
        mainheading = limited_content.filter_headings()[0]
        content.insert_after(mainheading, MosseAppreseBot.SUBPAGE_INCLUSION)

        # Uploading the page if necessary
        self.userPut(page=page, oldtext=page.text, newtext=str(content),
                     summary=self.summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # Summary message, whether to accept all uploads
    summary, always = None, False

    genFactory = pagegenerators.GeneratorFactory()

    # Processing all global bot args
    local_args = pwb.handle_args(args)

    # Processing all non-global CLI arguments
    for arg in local_args:
        if genFactory.handle_arg(arg):
            continue

        # By convention, all the arguments not starting with - are considered
        # positional.
        if not arg.startswith('-'):
            headings.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(':')

        if arg_name == 'always':
            always = True
        elif arg_name == 'summary':
            summary = arg_value

    bot = MosseAppreseBot(
        always=always,
        summary=summary,
        generator=genFactory.getCombinedGenerator(),
    )
    bot.run()

if __name__ == '__main__':
    main()
