#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This bot updates learnlist for the given Pokémon to a specified generation.

It expects learnlists to be located in subpage "/Mosse apprese in n-th gen",
and does the following operations:
- if needed, create the subpage for the specified generation
- update the subpage using the output of a specified command
- update the Pokémon page to point to the right subpage
This last step is optional, and can be suppressed with the option -subpage-only

Options:
    -subpage-only  suppress update of the main Pokémon page, only processes
                   subpages

The first two positional arguments are, respectively, the lua script to run
(that is expected to be `wiki-util/pokemoves-autogen/get-learnlist.lua`) and
the generation.

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

# Constant with gen name and number
GENERATIONS = {
    8: {"text": "ottava", "roman": "VIII", "number": 8},
    9: {"text": "nona", "roman": "IX", "number": 9},
}

# This is required for the text that is shown when you run this script with the
# parameter -help.
docuReplacements = {"&pagegenerator-params;": pagegenerators.parameterHelp}


class UpdateLearnlistSubpagesBot(SingleSiteBot):
    SUBPAGE_TITLE = "{poke}/Mosse apprese in {gen_text} generazione"
    SUBPAGE_INC_REGEX = "{{/Mosse apprese in [\w]+ generazione}}"
    SUBPAGE_INC_REPL = "/Mosse apprese in {gen_text} generazione"

    # Constants specifying which sections to treat and parameters for the command
    SECTIONS = [
        ("Aumentando di \[\[livello\]\]", "level"),
        ("Tramite \[\[MT\]\]/\[\[DT\]\]", "tm"),
        ("Tramite \[\[MT\]\]", "tm"),
        ("Tramite \[\[MT\]\]/\[\[MN\]\]", "tm"),
        ("Tramite \[\[Accoppiamento Pokémon\|accoppiamento\]\]", "breed"),
        ("Dall'\[\[Insegnamosse\]\]", "tutor"),
        ("Tramite \[\[evoluzione\|evoluzioni\]\] precedenti", "preevo"),
    ]

    NOINCLUDE_CATS = """<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({gen_text} generazione)]]
[[en:{poke} (Pokémon)/Generation {gen_roman} learnset]]
</noinclude>"""

    # Content of an empty subpage, to be filled by self.replace_learnlists
    EMPTY_SUBPAGE = """
====Aumentando di [[livello]]====
====Tramite [[MT]]====
====Tramite [[Accoppiamento Pokémon|accoppiamento]]====
====Dall'[[Insegnamosse]]====
====Tramite [[evoluzione|evoluzioni]] precedenti====
<noinclude>
[[Categoria:Sottopagine moveset Pokémon ({gen_text} generazione)]]
[[en:{poke} (Pokémon)/Generation {gen_roman} learnset]]
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
    @param subpage_only: Whether to suppress edit of the Pokémon page
    @type subpage_only: bool
    """

    def __init__(
        self,
        summary: str,
        command_path: str,
        generation: int,
        subpage_only: bool,
        **kwargs
    ):
        """Initializer."""
        super(UpdateLearnlistSubpagesBot, self).__init__(**kwargs)

        self.command_path = command_path
        self.subpage_only = subpage_only
        self.summary = summary or "Bot: updating learnlists"
        self.generation = GENERATIONS[generation]

    def format_gen(self, s, **kwargs):
        """Fixes the generation in a text.

        For cenvenience, this also accepts other substitutions to pass to
        string.format
        """
        return s.format(
            gen_text=self.generation["text"],
            gen_roman=self.generation["roman"],
            gen_number=self.generation["number"],
            **kwargs
        )

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
            noinclude_cats = content.filter_tags(
                recursive=False, matches=lambda c: str(c.tag) == "noinclude"
            )[0]
            links = noinclude_cats.contents.filter_wikilinks(recursive=False)
            cat = list(
                filter(
                    lambda c: str(c.title).startswith(("Categoria:", "Category:")),
                    links,
                )
            )[0]
            content.remove(noinclude_cats)
        except IndexError:
            # Here something went wrong, hence rebuild the final noinclude
            pwb.warning(
                "Problems finding the final noinclude, rebuilding from scratches"
            )
            noinclude_cats = mwparser.parse(
                self.format_gen(UpdateLearnlistSubpagesBot.NOINCLUDE_CATS, poke=poke)
            )
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
                gen = self.generation["number"]
                subout = subprocess.run(
                    ["lua", self.command_path, poke, kind, str(gen)],
                    capture_output=True,
                    encoding="utf-8",
                )
                try:
                    subout.check_returncode()
                except CalledProcessError:
                    pwb.error("The lua subprocess encountered an error")
                    pwb.error(subout.stderr)
                    raise
                newcontent = subout.stdout
                if newcontent.strip() != "":
                    content.replace(
                        section, str(real_heading) + "\n" + newcontent + "\n"
                    )
                else:
                    content.remove(section)

        # Adding category and interwiki
        content.append(noinclude_cats)

        # Uploading the page if necessary
        oldtext = oldtext or page.text
        self.userPut(
            page=page, oldtext=oldtext, newtext=str(content), summary=self.summary
        )

    def treat(self, page):
        """Treats a single page.

        It performs what described above, so:
        - possibly creates the subpage
        - runs ReplaceLearnlistsBot on it
        - (possibly) replace the inclusion in the main page
        """
        poke = UpdateLearnlistSubpagesBot.get_poke_name(page)
        gen = self.generation["number"]
        # Look for the subpage and possibly create it
        llsubpagelink = BaseLink(
            self.format_gen(UpdateLearnlistSubpagesBot.SUBPAGE_TITLE, poke=poke),
            site=self.site,
        )
        llsubpage = Page(llsubpagelink)
        if not llsubpage.exists():
            llsubpage.text = self.format_gen(
                UpdateLearnlistSubpagesBot.EMPTY_SUBPAGE, poke=poke
            )
        # Here the subpage is guaranteed to exists, so replace_learnlists on it
        self.replace_learnlists(llsubpage, oldtext="")
        # Possibly change the inclusion in the main page
        if not self.subpage_only:
            repl = (
                "{{"
                + self.format_gen(UpdateLearnlistSubpagesBot.SUBPAGE_INC_REPL)
                + "}}"
            )
            newtext = re.sub(
                UpdateLearnlistSubpagesBot.SUBPAGE_INC_REGEX, repl, page.text
            )
            self.userPut(
                page=page, oldtext=page.text, newtext=newtext, summary=self.summary
            )


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # Summary message, whether to accept all uploads
    summary, always, subpage_only = None, False, False

    genFactory = pagegenerators.GeneratorFactory()

    # Processing all global bot args
    local_args = pwb.handle_args(args)

    # Positional args
    pos_args = []

    # Processing all non-global CLI arguments
    for arg in local_args:
        if genFactory.handle_arg(arg):
            continue

        # All the arguments not starting with "-" are considered positional.
        if not arg.startswith("-"):
            pos_args.append(arg)
            continue

        arg_name, _, arg_value = arg[1:].partition(":")

        if arg_name == "always":
            always = True
        elif arg_name == "summary":
            summary = arg_value
        elif arg_name == "subpage-only":
            subpage_only = True

    bot = UpdateLearnlistSubpagesBot(
        always=always,
        summary=summary,
        subpage_only=subpage_only,
        generator=genFactory.getCombinedGenerator(),
        command_path=pos_args[0],
        generation=int(pos_args[1]),
    )
    bot.run()


if __name__ == "__main__":
    main()
