#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2004-2019
#
# Distributed under the terms of the MIT license.
#
"""
Script to download an image from a Wiki.

Usage:

    python pwb.py imagedownload (<pagename>|<generator>) [<options>]

NOTE: <pagename> SHOULD contain the namespace prefix (ie: File or its translations);
<generator> can be any supported page generator (e.g. -cat:'<category name>')

If pagename is an image description page, simply downloads it. If it is
a normal page, it will offer to copy any of the images used on that page,
or if the -interwiki argument is used, any of the images used on a page
reachable via interwiki links.
"""

import itertools
import os
import os.path
import tempfile

import pywikibot
from pywikibot import pagegenerators

from utils.PcwCliArgs import PcwCliArgs


class ImageTransferBot(object):
    def __init__(
        self,
        generator,
        target_dir,
        interwiki=False,
    ):
        self.generator = generator
        self.interwiki = interwiki
        self.site_image_repository = pywikibot.Site().image_repository()
        self.target_dir = target_dir
        os.makedirs(self.target_dir, exist_ok=True)

    def transferImage(self, sourceImagePage):
        target_file = os.path.join(self.target_dir, sourceImagePage._link._title)
        sourceImagePage.download(target_file)
        pywikibot.output(f"Downloaded file to {target_file}")

    def showImageList(self, imagelist):
        for i, image in enumerate(imagelist):
            pywikibot.output("-" * 60)
            pywikibot.output(f"{i}. Found image: {image.title(as_link=True)}")
        pywikibot.output("=" * 60)

    def run(self):
        """Run the bot."""
        for page in self.generator:
            if self.interwiki:
                interwikis = map(pywikibot.Page, page.interwiki())
                imagelist = list(itertools.chain.from_iterable(interwikis))
            elif page.is_filepage():
                imagelist = [pywikibot.FilePage(page.site, page.title())]
            else:
                imagelist = list(page.imagelinks())

            while imagelist:
                self.showImageList(imagelist)
                if len(imagelist) == 1:
                    # no need to query the user, only one possibility
                    todo = 0
                else:
                    pywikibot.output("Give the number of the image to transfer.")
                    todo = pywikibot.input("To end uploading, press enter:")
                    if not todo:
                        break
                    todo = int(todo)

                try:
                    chosen_image = imagelist[todo]
                    is_from_site = (
                        chosen_image.site.image_repository()
                        == self.site_image_repository
                    )
                    imagelist.remove(chosen_image)
                    if chosen_image.file_is_shared() and is_from_site:
                        pywikibot.output(
                            f"The image is already shared on {self.site_image_repository}."
                        )
                    else:
                        self.transferImage(imagelist[todo])
                except IndexError:
                    pywikibot.output("No such image number.")


def main():
    args = (
        PcwCliArgs(__doc__, ending=pagegenerators.parameterHelp)
        .flag("interwiki", "List images reachable via interwiki links")
        .opt(
            "target",
            "dir",
            "The directory where the images will be saved",
            default=tempfile.gettempdir(),
        )
    )
    args.parse(
        include_pwb=True,
        gen_factory=pagegenerators.GeneratorFactory(positional_arg_name="page"),
    )

    gen = args.gen_factory.getCombinedGenerator()
    if not gen:
        pywikibot.bot.suggest_help(
            missing_parameters=["page"],
            additional_text="and no other generator was defined.",
        )
        return

    bot = ImageTransferBot(
        gen,
        interwiki=args.parsed["interwiki"],
        target_dir=os.path.abspath(args.parsed["target"]),
    )
    bot.run()


if __name__ == "__main__":
    main()
