#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys

import pywikibot as pwb
from altforms import AltForms
from LearnlistSubpageBot import LearnlistSubpageBot
from lpza import map_datamine


def main(args: list[str]):
    [datamine_file, alt_forms_file, out_dir] = pwb.handle_args(args)
    alt_forms = AltForms.from_json(alt_forms_file)
    print(list(map(type, alt_forms.keys())))
    # LearnlistSubpageBot(
    #     alt_forms=alt_forms,
    #     it_gen_ord="nona",
    #     out_dir=out_dir,
    #     roman_gen="IX",
    #     summary="Add LPZA learnlists",
    #     generator=map_datamine("learnlist", datamine_file),
    # ).run()


if __name__ == "__main__":
    main(sys.argv[1:])
