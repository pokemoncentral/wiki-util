#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to download an image from a Wiki.

Syntax:

    python pwb.py imagedownload {<pagename>|<generator>} [<options>]

NOTE: <pagename> SHOULD contain the namespace prefix (ie: File o its translations)

The following parameters are supported:

  -target:z    Target directory for the download

If pagename is an image description page, simply downloads it. If it is
a normal page, it will offer to copy any of the images used on that page,
or if the -interwiki argument is used, any of the images used on a page
reachable via interwiki links.

&params;
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2004-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re
import sys
import os
import urllib.request

import pywikibot

from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.specialbots import UploadRobot


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class ImageTransferBot(object):

    """Image transfer bot."""

    def __init__(self, generator, targetSite=None, interwiki=False,
                 ignore_warning=False, target_dir="/tmp"):
        """Initializer."""
        self.generator = generator
        self.interwiki = interwiki
        self.targetSite = targetSite
        self.ignore_warning = ignore_warning
        self.target_dir = target_dir

    def transferImage(self, sourceImagePage):
        """
        Download image and its description.

        @return: None
        """
        url = sourceImagePage.get_file_url()
        target_file = os.path.join(self.target_dir, sourceImagePage._link._title)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with open(target_file, "wb") as outfile, urllib.request.urlopen(req) as infile:
            outfile.write(infile.read())
        pywikibot.output("Downloaded file to {}".format(target_file))

    def showImageList(self, imagelist):
        """Print image list."""
        for i, image in enumerate(imagelist):
            pywikibot.output('-' * 60)
            pywikibot.output('{}. Found image: {}'
                             .format(i, image.title(as_link=True)))
            # try:
            #     # Show the image description page's contents
            #     # pywikibot.output(image.get())
            #     # look if page already exists with this name.
            #     # TODO: consider removing this: a different image of the same
            #     # name may exist on the target wiki, and the bot user may want
            #     # to upload anyway, using another name.
            #     # try:
            #     #     # Maybe the image is on the target site already
            #     #     targetTitle = 'File:' + image.title().split(':', 1)[1]
            #     #     targetImage = pywikibot.Page(self.targetSite, targetTitle)
            #     #     targetImage.get()
            #     #     pywikibot.output('Image with this name is already on {}.'
            #     #                      .format(self.targetSite))
            #     #     pywikibot.output('-' * 60)
            #     #     pywikibot.output(targetImage.get())
            #     #     sys.exit()
            #     # except pywikibot.NoPage:
            #     #     # That's the normal case
            #     #     pass
            #     # except pywikibot.IsRedirectPage:
            #     #     pywikibot.output(
            #     #         'Description page on target wiki is redirect?!')
            #     pass
            # except pywikibot.NoPage:
            #     break
        pywikibot.output('=' * 60)

    def run(self):
        """Run the bot."""
        for page in self.generator:
            if self.interwiki:
                imagelist = []
                for linkedPage in page.interwiki():
                    linkedPage = pywikibot.Page(linkedPage)
                    imagelist.extend(
                        linkedPage.imagelinks(
                            followRedirects=True))
            elif page.is_filepage():
                imagePage = pywikibot.FilePage(page.site, page.title())
                imagelist = [imagePage]
            else:
                imagelist = list(page.imagelinks(followRedirects=True))

            while imagelist:
                self.showImageList(imagelist)
                if len(imagelist) == 1:
                    # no need to query the user, only one possibility
                    todo = 0
                else:
                    pywikibot.output(
                        'Give the number of the image to transfer.')
                    todo = pywikibot.input('To end uploading, press enter:')
                    if not todo:
                        break
                    todo = int(todo)
                if todo in range(len(imagelist)):
                    if (imagelist[todo].fileIsShared()
                            and imagelist[todo].site.image_repository()
                            == self.targetSite.image_repository()):
                        pywikibot.output(
                            'The image is already shared on {0}.'
                            .format(self.targetSite.image_repository()))
                    else:
                        self.transferImage(imagelist[todo])
                    # remove the selected image from the list
                    imagelist = imagelist[:todo] + imagelist[todo + 1:]
                else:
                    pywikibot.output('No such image number.')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    interwiki = False
    keep_name = False
    targetLang = None
    targetFamily = None

    local_args = pywikibot.handle_args(args)
    generator_factory = pagegenerators.GeneratorFactory(
        positional_arg_name='page')

    for arg in local_args:
        if arg == '-interwiki':
            interwiki = True
        elif arg.startswith('-keepname'):
            keep_name = True
        # elif arg.startswith('-tolang:'):
        #     targetLang = arg[8:]
        # elif arg.startswith('-tofamily:'):
        #     targetFamily = arg[10:]
        elif arg.startswith('-target:'):
            targetDir = arg[8:]
        else:
            generator_factory.handleArg(arg)

    gen = generator_factory.getCombinedGenerator()
    if not gen:
        pywikibot.bot.suggest_help(
            missing_parameters=['page'],
            additional_text='and no other generator was defined.')
        return False

    site = pywikibot.Site()
    # if not targetLang and not targetFamily:
    #     targetSite = site.image_repository()
    # else:
    targetSite = pywikibot.Site(targetLang or site.lang,
                                targetFamily or site.family)
    bot = ImageTransferBot(gen, interwiki=interwiki, targetSite=targetSite,
                           target_dir=targetDir)
    bot.run()


if __name__ == '__main__':
    main()
