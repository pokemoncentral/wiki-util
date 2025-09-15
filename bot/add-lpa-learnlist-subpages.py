#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot adds LPA learnlist to the given Pokémon.

It examine the subpage "/Mosse apprese in ottava generazione" and adds to the
right subsection (ie. level and tutor) the new learnlist for LPA moves. Note
that whenever it finds something unexpected in a page (such as more than one
form), it conservatively abort and log the error.

Also note that calling this script requires to parse the datamine file, so a
single call on many pages is more efficient than many calls on single pages.

These command line parameters can be used to specify which pages to work on:

&pagegenerator-params;
"""

import re

import mwparserfromhell as mwparser
import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot.bot import SingleSiteBot
from pywikibot.page import BaseLink, Page

from utils.PcwCliArgs import PcwCliArgs

# This is required for the text that is shown when you run this script with the
# parameter -help.
docuReplacements = {"&pagegenerator-params;": pagegenerators.parameterHelp}

# Should integrate this with pwb's logging facility, but I can't find
# documentation online
import logging

logger = logging.getLogger("log")
file_lh = logging.FileHandler("/tmp/cusu.log")
file_lh.setLevel(logging.WARNING)
logger.addHandler(file_lh)


class DatamineParser:
    REPLACES = {
        "mr.-mime": "mr. mime",
        "mr.-mime-1": "mr. mimeG",
        "mime-jr.": "mime jr.",
        "mr.-rime": "mr. rime",
        "pikachu": "pikachu",
        "pikachu-1": "pikachuO",
        "pikachu-2": "pikachuH",
        "pikachu-3": "pikachuSi",
        "pikachu-4": "pikachuU",
        "pikachu-5": "pikachuK",
        "pikachu-6": "pikachuA",
        "pikachu-7": "pikachuCo",
        "raichu": "raichu",
        "raichu-1": "raichuA",
        "darumaka": "darumaka",
        "darumaka-1": "darumakaG",
        "darmanitan": "darmanitan",
        "darmanitan-1": "darmanitanZ",
        "darmanitan-2": "darmanitanG",
        "darmanitan-3": "darmanitanGZ",
        "vulpix": "vulpix",
        "vulpix-1": "vulpixA",
        "ninetales": "ninetales",
        "ninetales-1": "ninetalesA",
        "diglett": "diglett",
        "diglett-1": "diglettA",
        "dugtrio": "dugtrio",
        "dugtrio-1": "dugtrioA",
        "meowth": "meowth",
        "meowth-1": "meowthA",
        "meowth-2": "meowthG",
        "persian": "persian",
        "persian-1": "persianA",
        "ponyta": "ponyta",
        "ponyta-1": "ponytaG",
        "rapidash": "rapidash",
        "rapidash-1": "rapidashG",
        "weezing": "weezing",
        "weezing-1": "weezingG",
        "corsola": "corsola",
        "corsola-1": "corsolaG",
        "zigzagoon": "zigzagoon",
        "zigzagoon-1": "zigzagoonG",
        "linoone": "linoone",
        "linoone-1": "linooneG",
        "stunfisk": "stunfisk",
        "stunfisk-1": "stunfiskG",
        "farfetch'd": "farfetchd",
        "farfetch’d": "farfetchd",
        "farfetch'd-1": "farfetchdG",
        "farfetch’d-1": "farfetchdG",
        "sirfetch'd": "sirfetchd",
        "sirfetch’d": "sirfetchd",
        "cramorant": "cramorant",
        "cramorant-1": "cramorantT",
        "cramorant-2": "cramorantI",
        "toxtricity": "toxtricity",
        "toxtricity-1": "toxtricityB",
        "eiscue": "eiscue",
        "eiscue-1": "eiscueL",
        "indeedee": "indeedee",
        "indeedee-1": "indeedeeF",
        "morpeko": "morpeko",
        "morpeko-1": "morpekoV",
        "zacian": "zacian",
        "zacian-1": "zacianR",
        "zamazenta": "zamazenta",
        "zamazenta-1": "zamazentaR",
        "eternatus": "eternatus",
        "eternatus-1": "eternatusD",
        "shellos": "shellos",
        "gastrodon": "gastrodon",
        "cherrim": "cherrim",
        "sinistea": "sinistea",
        "sinistea-1": "sinisteaA",
        "polteageist": "polteageist",
        "polteageist-1": "polteageistA",
        "alcremie": "alcremie",
        "alcremie-1": "alcremieR",
        "alcremie-2": "alcremieMa",
        "alcremie-3": "alcremieMe",
        "alcremie-4": "alcremieL",
        "alcremie-5": "alcremieS",
        "alcremie-6": "alcremieRm",
        "alcremie-7": "alcremieCm",
        "alcremie-8": "alcremieTm",
        "mimikyu": "mimikyu",
        "mimikyu-1": "mimikyuS",
        "silvally": "silvally",  # TODO silvally
        "silvally-1": "silvally",
        "silvally-2": "silvally",
        "silvally-3": "silvally",
        "silvally-4": "silvally",
        "silvally-5": "silvally",
        "silvally-6": "silvally",
        "silvally-7": "silvally",
        "silvally-8": "silvally",
        "silvally-9": "silvally",
        "silvally-10": "silvally",
        "silvally-11": "silvally",
        "silvally-12": "silvally",
        "silvally-13": "silvally",
        "silvally-14": "silvally",
        "silvally-15": "silvally",
        "silvally-16": "silvally",
        "silvally-17": "silvally",
        "type:null": "tipo zero",
        "type:-null": "tipo zero",
        "necrozma": "necrozma",
        "necrozma-1": "necrozmaV",
        "necrozma-2": "necrozmaA",
        "wishiwashi": "wishiwashi",
        "wishiwashi-1": "wishiwashiB",
        "pumpkaboo": "pumpkaboo",
        "pumpkaboo-1": "pumpkabooS",
        "pumpkaboo-2": "pumpkabooL",
        "pumpkaboo-3": "pumpkabooXL",
        "gourgeist": "gourgeist",
        "gourgeist-1": "gourgeistS",
        "gourgeist-2": "gourgeistL",
        "gourgeist-3": "gourgeistXL",
        "aegislash": "aegislash",
        "aegislash-1": "aegislashS",
        "meowstic": "meowstic",
        "meowstic-1": "meowsticF",
        "keldeo": "keldeo",
        "keldeo-1": "keldeoR",
        "kyurem": "kyurem",
        "kyurem-1": "kyuremN",
        "kyurem-2": "kyuremB",
        "yamask": "yamask",
        "yamask-1": "yamaskG",
        "basculin": "basculin",
        "basculin-1": "basculinB",
        "rotom": "rotom",
        "rotom-1": "rotomC",
        "rotom-2": "rotomL",
        "rotom-3": "rotomG",
        "rotom-4": "rotomV",
        "rotom-5": "rotomT",
        "exeggutor-1": "exeggutorA",
        "marowak-1": "marowakA",
        "sandshrew-1": "sandshrewA",
        "sandslash-1": "sandslashA",
        "slowpoke-1": "slowpokeG",
        "slowbro-2": "slowbroG",
        "slowking-1": "slowkingG",
        "lycanroc": "lycanroc",
        "lycanroc-1": "lycanrocN",
        "lycanroc-2": "lycanrocC",
        "urshifu-1": "urshifuP",
        "articuno-1": "articunoG",
        "zapdos-1": "zapdosG",
        "moltres-1": "moltresG",
        "calyrex-1": "calyrexG",
        "calyrex-2": "calyrexS",
        "giratina-1": "giratinaO",
        "tornadus-1": "tornadusT",
        "thundurus-1": "thundurusT",
        "landorus-1": "landorusT",
        "zygarde-1": "zygardeD",
        "zygarde-4": "zygardeP",
        "tapu-koko": "tapu koko",
        "tapu-lele": "tapu lele",
        "tapu-bulu": "tapu bulu",
        "tapu-fini": "tapu fini",
        "zarude-1": "zarudeP",
        "growlithe-1": "growlitheH",
        "arcanine-1": "arcanineH",
        "voltorb-1": "voltorbH",
        "electrode-1": "electrodeH",
        "typhlosion-1": "typhlosionH",
        "qwilfish-1": "qwilfishH",
        "sneasel-1": "sneaselH",
        "wormadam-1": "wormadamSa",
        "wormadam-2": "wormadamSc",
        "dialga-1": "dialgaO",
        "palkia-1": "palkiaO",
        "shaymin-1": "shayminC",
        "samurott-1": "samurottH",
        "lilligant-1": "lilligantH",
        "basculin-2": "basculinH",
        "zorua-1": "zoruaH",
        "zoroark-1": "zoroarkH",
        "braviary-1": "braviaryH",
        "sliggoo-1": "sliggooH",
        "goodra-1": "goodraH",
        "avalugg-1": "avaluggH",
        "decidueye-1": "decidueyeH",
    }

    @staticmethod
    def normalize_pokename(poke):
        poke = poke.strip().lower().replace(" ", "-")
        if poke in DatamineParser.REPLACES:
            return DatamineParser.REPLACES[poke]
        else:
            return poke

    @staticmethod
    def split_moves(lines):
        """Return a Tuple[List[str], List[str]]
        These are lists of moves learned by level and tutor respectively
        """
        res = []
        for fline in ("Level:", "Move Shop:"):
            try:
                idx = lines.index(fline) + 1
                moves = []
                while idx < len(lines) and lines[idx].startswith("- "):
                    moves.append(lines[idx])
                    idx += 1
                res.append(moves)
            except ValueError:
                res.append([])
        # Reorder res to have the expected order
        return tuple(res)

    @staticmethod
    def parse_move_line(line, kind):
        if kind == 0:  # level
            # - Confusione @ 0, mastered @ 15
            regex = r"^- \[(\d{1,3})\] \[(\d{1,3})\] (.*)$"
        elif kind == 1:  # tutor
            regex = r"^- (.*)$"

        m = re.match(regex, line.strip())
        if not m:
            logger.error("Line of kind {} doesn't match the regex".format(kind))
            logger.error(line)
            exit(1)

        res = m.groups()
        if kind == 0:
            res = (res[2], res[0], res[1])
        return res

    @staticmethod
    def all_pokes_info(filename):
        res = {}
        with open(filename, "r") as f:
            pokelines = []
            move = ""
            for line in f:
                line = line.strip()
                if line == "":  # Empty lines are the separators
                    pokename = DatamineParser.normalize_pokename(pokelines[0])
                    if re.search(r"-\d+$", pokename):
                        pwb.warning(
                            '{} name ends in "-number". This may point to a missing replacement'.format(
                                pokename
                            )
                        )
                    # logger.info(pokename)

                    moves_by_kind = DatamineParser.split_moves(pokelines)
                    parsed_moves = list(
                        list(map(lambda l: DatamineParser.parse_move_line(l, i), lines))
                        for i, lines in enumerate(moves_by_kind)
                    )
                    # logger.debug(str(list(parsed_moves)))
                    res[pokename] = parsed_moves
                    pokelines = []
                else:
                    pokelines.append(line)
        return res

    def __init__(self, filename):
        self.info = DatamineParser.all_pokes_info(filename)

    OUTPUT_LINES = (
        "|{}|||{}|{}| //",  # 0 -> level
        "|{}|||yes| //",  # 1 -> tutor
    )

    KIND_NAME = (
        "level",  # 0 -> level
        "tutor",  # 1 -> tutor
    )

    def get_learnlists(self, poke, kind):
        """Returns the learnlist call for the given input."""
        parsed_moves = self.info[poke.lower()][kind]
        kindname = DatamineParser.KIND_NAME[kind]
        res = "{{{{#invoke: Learnlist/hf | {}hLPA | {} | 8 }}}}\n".format(
            kindname, poke
        )
        res += "{{{{#invoke: render | render | Modulo:Learnlist/entry8LPA | {} | //\n".format(
            kindname
        )
        res += "".join(
            map(
                lambda move: DatamineParser.OUTPUT_LINES[kind].format(*move) + "\n",
                parsed_moves,
            )
        )
        res += "}}\n"
        res += "{{{{#invoke: Learnlist/hf | {}fLPA | {} | 8 }}}}\n".format(
            kindname, poke
        )
        return res


# Global constant for generation
GENERATION = "ottava"


class UpdateLearnlistSubpagesBot(SingleSiteBot):
    SUBPAGE_TITLE = "{poke}/Mosse apprese in {gen} generazione"
    SUBPAGE_INC_REGEX = r"{{/Mosse apprese in [\w]+ generazione}}"
    SUBPAGE_INC_REPL = "/Mosse apprese in {gen} generazione"

    # Constants specifying which sections to treat and parameters for the command
    SECTIONS = [
        (r"Aumentando di \[\[livello\]\]", 0),
        (r"Dall'\[\[Insegnamosse\]\]", 1),
    ]

    # Content of an empty subpage, to be filled by self.replace_learnlists
    EMPTY_SUBPAGE = """====Aumentando di [[livello]]====
====Dall'[[Insegnamosse]]====
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

    """A bot that adds LPA to learnlists subpages.

    @param summary: The edit message.
    @type summary: str
    @param datamine_file: The path to the datamine file
    @type command_path: str
    """

    def __init__(self, summary, datamine_file, **kwargs):
        """Initializer."""
        super(UpdateLearnlistSubpagesBot, self).__init__(**kwargs)

        self.summary = summary or "Bot: adding LPA learnlists"
        self.datamine = DatamineParser(datamine_file)

    def add_learnlists(self, page):
        """Add LPA learnlists to the right sections in the given page.

        If anything goes wrong, abort, otherwise save the page at then end.
        "Going wrong" means that either a learnlist for LPA is already in the
        section or the section doesn't just contain a single learnlist. This in
        particular means no support for alternative forms.
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
            pwb.warning("Problems finding the final noinclude, aborting")
            logger.warning("Pokémon {} had issues".format(poke))
            return

        # For any heading to process
        try:
            limited_content = content.get_sections(matches="Mosse apprese")[0]
        except IndexError:
            limited_content = content
        for heading, kind in UpdateLearnlistSubpagesBot.SECTIONS:
            for section in limited_content.get_sections(matches=heading):
                if len(section.filter_headings()) > 1:
                    # More than one heading, so skip the section
                    pwb.warning(
                        "Found more than one subsection for kind {}: aborting".format(
                            kind
                        )
                    )
                    logger.warning("Pokémon {} had issues".format(poke))
                    continue
                real_heading = section.filter_headings()[0]
                if (
                    len(
                        section.filter_templates(
                            matches=lambda t: t.name.lower().strip()
                            == "#invoke: learnlist/hf"
                            and t.get(1).find("LPA") != -1
                        )
                    )
                    > 0
                ):
                    pwb.warning(
                        "Found something that looks like the LPA learnlist for kind {}, skipping".format(
                            kind
                        )
                    )
                    continue
                newcontent = self.datamine.get_learnlists(poke, kind).strip()
                section.append("\n")
                section.append(newcontent + "\n")

        # Adding category and interwiki
        content.append(noinclude_cats)

        # Writing the page to file, ready to be uploaded
        with open("/tmp/newpages/{}".format(poke), "w") as ofile:
            ofile.write("{{{{-start-}}}}\n'''{}'''\n".format(page.title()))
            ofile.write(str(content))
            ofile.write("\n{{{{-stop-}}}}")
        # Uploading the page if necessary
        self.userPut(
            page=page, oldtext=page.text, newtext=str(content), summary=self.summary
        )

    def treat(self, page):
        """Treats a single page."""
        poke = UpdateLearnlistSubpagesBot.get_poke_name(page)
        # Look for the subpage and possibly create it
        llsubpagelink = BaseLink(
            UpdateLearnlistSubpagesBot.SUBPAGE_TITLE.format(poke=poke, gen=GENERATION),
            site=self.site,
        )
        llsubpage = Page(llsubpagelink)
        if not llsubpage.exists():
            create = pwb.input_yn(
                "Subpage doesn't exists: should I create it?", default=True
            )
            if not create:
                return
            llsubpage.text = UpdateLearnlistSubpagesBot.EMPTY_SUBPAGE.format(
                poke=poke, gen=GENERATION
            )
        # Here the subpage is guaranteed to exists, so add_learnlists on it
        self.add_learnlists(llsubpage)


def main():
    args = PcwCliArgs(__doc__).pos("DATAMINE-FILE", "The name of the datamine file")
    args.parse(include_pwb=True)

    bot = UpdateLearnlistSubpagesBot(
        datamine_file=args[0],
        always=args.parsed["always"],
        summary=args.parsed["summary"],
        generator=args.gen_factory.getCombinedGenerator(),
    )
    bot.run()


if __name__ == "__main__":
    main()
