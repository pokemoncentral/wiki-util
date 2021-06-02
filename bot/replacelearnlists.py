#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot replaces learnlists with the output of a command.
Just call it with a generator that yields Pokémon's pages, and it does the
rest on its own.

Pls don't bother me with "everything is hardcoded bad practice blablabla"
because right now I don't have time to do something nice, and I know in
the future I won't change it.
Moreover the command is meant to be run once in a while and the hardcoded part
doesn't change.

&pagegenerator-params;
"""

import codecs
import re
import os
import subprocess
from functools import partial
from itertools import dropwhile

import mwparserfromhell as mwparser
import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot.bot import (
    ExistingPageBot, FollowRedirectPageBot, MultipleSitesBot,
    QuitKeyboardInterrupt
)

# This is required for the text that is shown when you run this script with the
# parameter -help.
docuReplacements = {'&pagegenerator-params;': pagegenerators.parameterHelp}


class SectionsBot(MultipleSitesBot, ExistingPageBot, FollowRedirectPageBot):
    # Constants specifying which sections to treat and parameters for the command
    SECTIONS = [
        ("Aumentando di \[\[livello\]\]", "level"),
        ("Tramite \[\[MT\]\]/\[\[DT\]\]", "tm"),
        ("Tramite \[\[MT\]\]", "tm"),
        ("Tramite \[\[MT\]\]/\[\[MN\]\]", "tm"),
        ("Tramite \[\[Accoppiamento Pokémon\|accoppiamento\]\]", "breed"),
        ("Dall'\[\[Insegnamosse\]\]", "tutor"),
        ("Tramite \[\[evoluzione\|evoluzioni\]\] precedenti", "preevo")
    ]

    NOINCLUDE_CATS = """<noinclude>
[[Categoria:Sottopagine moveset Pokémon (ottava generazione)]]
[[en:{poke} (Pokémon)/Generation VIII learnset]]
</noinclude>"""

    """A bot that replaces sections with the output of a certain script

    @param summary: The edit message.
    @type summary: str
    @param command_path: The path to the command to execute
    @type command_path: str
    @keyword always: Whether to prompt the user before uploading changes.
    @type always: bool
    """
    def __init__(self, summary, command_path, **kwargs):
        """Initializer."""
        super(SectionsBot, self).__init__(**kwargs)

        self.command_path = command_path
        self.summary = (summary or 'Bot: replacing learnlists')


    def treat(self, page):
        """Replaces the content of each section in the list with the output
        of a certain command, whose arguments are the page title and
        anything determined by the section
        """
        # Get roottitle
        rootidx = page.title().find("/")
        roottitle = page.title() if rootidx == -1 else page.title()[:rootidx]

        # Parsing the page
        content = mwparser.parse(page.text, skip_style_tags=True)

        # Getting the final noinclude
        try:
            noinclude_cats = content.filter_tags(recursive=False, matches=lambda c: str(c.tag) == "noinclude")[0]
            links = noinclude_cats.contents.filter_wikilinks(recursive=False)
            cat = list(filter(lambda c: str(c.title).startswith(("Categoria:", "Category:")), links))[0]
            content.remove(noinclude_cats)
        except IndexError:
            # Here something went wrong, hence rebuild the final noinclude
            pywikibot.warning("Problems finding the final noinclude, rebuilding from scratches")
            noinclude_cats = mwparser.parse(NOINCLUDE_CATS.format(poke=roottitle))
            pywikibot.output(noinclude_cats)
            rebuild = pywikibot.input_yn("Is this correct?", default=True)
            if not rebuild:
                raise QuitKeyboardInterrupt()

        # For any heading to process
        try:
            limited_content = content.get_sections(matches="Mosse apprese")[0]
        except IndexError:
            limited_content = content
        for heading, kind in SectionsBot.SECTIONS:
            for section in limited_content.get_sections(matches=heading):
                real_heading = section.filter_headings()[0]
                newcontent = subprocess.run(["lua", self.command_path, roottitle, kind], capture_output=True, encoding="utf-8")
                content.replace(section, str(real_heading) + "\n" + newcontent.stdout + "\n")

        # Adding category and interwiki
        content.append(noinclude_cats)

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

    bot = SectionsBot(
        always=always,
        summary=summary,
        generator=genFactory.getCombinedGenerator(),
        command_path="/path/to/wiki-util/pokemoves-autogen/get-learnlist.lua"
    )
    bot.run()

if __name__ == '__main__':
    main()
