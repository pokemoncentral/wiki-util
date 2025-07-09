import itertools

import mwparserfromhell as mwparser
import pywikibot as pwb
from pywikibot import pagegenerators
from pywikibot.bot import SingleSiteBot

"""
Add pads the ndex parameter in template rdex with 0s if it has less than 4 leading
digits.

"""


class FixRdexBot(SingleSiteBot):
    def __init__(self, summary: str, **kwargs):
        super(FixRdexBot, self).__init__(**kwargs)
        self.summary = summary or "Bot: 4-digits ndex in template rdex"

    def treat(self, page):
        """Treats a single page."""
        wikicode = mwparser.parse(page.text, skip_style_tags=True)
        # Iterate on all the rdex templates
        for rdex in wikicode.ifilter_templates(
            matches=lambda t: t.name.strip() == "rdex"
        ):
            ndex = str(rdex.get("2").value).strip()
            ld = sum(1 for _ in itertools.takewhile(lambda c: c.isdigit(), ndex))
            ndex = "0" * (4 - ld) + ndex
            rdex.add("2", ndex)
        # Save the changes
        self.userPut(
            page=page, oldtext=page.text, newtext=str(wikicode), summary=self.summary
        )


def main(*args):
    # parse args
    summary, always = None, False

    genFactory = pagegenerators.GeneratorFactory()

    # Processing all global bot args
    local_args = pwb.handle_args(args)

    # Processing all non-global CLI arguments
    for arg in local_args:
        if genFactory.handle_arg(arg):
            continue

        arg_name, _, arg_value = arg[1:].partition(":")

        if arg_name == "always":
            always = True
        elif arg_name == "summary":
            summary = arg_value

    bot = FixRdexBot(
        always=always, summary=summary, generator=genFactory.getCombinedGenerator()
    )
    bot.run()


if __name__ == "__main__":
    main()
