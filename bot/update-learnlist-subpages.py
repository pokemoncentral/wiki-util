#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot updates learnlist for the given Pokémon to a specified generation.

It expects learnlists to be located in subpage "/Mosse apprese in n-th gen",
and does the following operations:
- if needed, create the subpage for the specified generation
- update the subpage using the output of a specified command
- update the Pokémon page to point to the right subpage

The generation is currently hardcoded, but in a future update (when?) it will
be specified by a command line argument.

These command line parameters can be used to specify which pages to work on:

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
from pywikibot.bot import SingleSiteBot, ExistingPageBot
from pywikibot.page import Page, BaseLink

# Global constant for generation
GENERATION = "ottava"

# This is required for the text that is shown when you run this script with the
# parameter -help.
docuReplacements = {'&pagegenerator-params;': pagegenerators.parameterHelp}

class UpdateLearnlistSubpagesBot(SingleSiteBot):
    SUBPAGE_TITLE = "{poke}/Mosse apprese in {gen} generazione"
    SUBPAGE_INC_REGEX = "{{/Mosse apprese in [\w]+ generazione}}"
    SUBPAGE_INC_REPL = "/Mosse apprese in {gen} generazione"

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
[[Categoria:Sottopagine moveset Pokémon ({gen} generazione)]]
[[en:{poke} (Pokémon)/Generation VIII learnset]]
</noinclude>"""

    # Content of an empty subpage, to be filled by self.replace_learnlists
    EMPTY_SUBPAGE = """
====Aumentando di [[livello]]====
====Tramite [[MT]]====
====Tramite [[Accoppiamento Pokémon|accoppiamento]]====
====Dall'[[Insegnamosse]]====
====Tramite [[evoluzione|evoluzioni]] precedenti====
<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({gen} generazione)]]
[[en:{poke} (Pokémon)/Generation VIII learnset]]
</noinclude>
"""

    @staticmethod
    def get_poke_name(page):
        """Get the name of the Pokémon associated with a page.

        This works both in Pokémon pages and in their subpages.
        """
        rootidx = page.title().find("/")
        roottitle = page.title() if rootidx == -1 else page.title()[:rootidx]
        return roottitle

    """A bot that updates learnlists, provided they are in subpages.

    @param summary: The edit message.
    @type summary: str
    @param command_path: The path to the command to execute to get new learnlists
    @type command_path: str
    """
    def __init__(self, summary, command_path, **kwargs):
        """Initializer."""
        super(UpdateLearnlistSubpagesBot, self).__init__(**kwargs)

        self.command_path = command_path
        self.summary = (summary or 'Bot: replacing learnlists')

    def replace_learnlists(self, page, oldtext=None):
        """Replaces the content of each section in the list with the output
        of a certain command, whose arguments are the page title and
        anything determined by the section.
        At the end, it saves the page with the new content.
        """
        poke = UpdateLearnlistSubpagesBot.get_poke_name(page)

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
            pwb.warning("Problems finding the final noinclude, rebuilding from scratches")
            noinclude_cats = mwparser.parse(UpdateLearnlistSubpagesBot.NOINCLUDE_CATS.format(poke=poke, gen=GENERATION))
            pwb.output(noinclude_cats)
            rebuild = pwb.input_yn("Is this correct?", default=True)
            if not rebuild:
                raise QuitKeyboardInterrupt()

        # For any heading to process
        try:
            limited_content = content.get_sections(matches="Mosse apprese")[0]
        except IndexError:
            limited_content = content
        for heading, kind in UpdateLearnlistSubpagesBot.SECTIONS:
            for section in limited_content.get_sections(matches=heading):
                real_heading = section.filter_headings()[0]
                newcontent = subprocess.run(["lua", self.command_path, poke, kind], capture_output=True, encoding="utf-8").stdout
                if newcontent.strip() != "":
                    content.replace(section, str(real_heading) + "\n" + newcontent + "\n")
                else:
                    content.remove(section)

        # Adding category and interwiki
        content.append(noinclude_cats)

        # Uploading the page if necessary
        oldtext = oldtext or page.text
        self.userPut(page=page, oldtext=oldtext, newtext=str(content),
                     summary=self.summary)

    def treat(self, page):
        """Treats a single page.

        It performs what described above, so:
        - possibly creates the subpage
        - runs ReplaceLearnlistsBot on it
        - replace the inclusion in the main page
        """
        poke = UpdateLearnlistSubpagesBot.get_poke_name(page)
        # Look for the subpage and possibly create it
        llsubpagelink = BaseLink(UpdateLearnlistSubpagesBot.SUBPAGE_TITLE.format(poke=poke, gen=GENERATION), site=self.site)
        llsubpage = Page(llsubpagelink)
        if not llsubpage.exists():
            llsubpage.text = UpdateLearnlistSubpagesBot.EMPTY_SUBPAGE.format(poke=poke, gen=GENERATION)
        # Here the subpage is guaranteed to exists, so replace_learnlists on it
        self.replace_learnlists(llsubpage, oldtext="")
        # Possibly change the inclusion in the main page
        repl = "{{" + UpdateLearnlistSubpagesBot.SUBPAGE_INC_REPL.format(gen=GENERATION) + "}}"
        newtext = re.sub(UpdateLearnlistSubpagesBot.SUBPAGE_INC_REGEX,
                         repl,
                         page.text)
        self.userPut(page=page, oldtext=page.text, newtext=newtext, summary=self.summary)


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

    bot = UpdateLearnlistSubpagesBot(
        always=always,
        summary=summary,
        generator=genFactory.getCombinedGenerator(),
        command_path="/path/to/wiki-util/pokemoves-autogen/get-learnlist.lua"
    )
    bot.run()

if __name__ == '__main__':
    main()
