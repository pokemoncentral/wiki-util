#!/usr/bin/env python3

import os
import re
import sys

import pywikibot as pwb

LOCAL_MW = re.compile(
    r"""local mw = require\(['"]mw['"]\)(\n\s*\n)*""", flags=re.MULTILINE
)
LUA_REQUIRE = re.compile(r"""require\(['"](.+?)['"]\)""")


def local_file_to_module_content(file_name):
    with open(file_name, "r", encoding="utf-8") as lua_module_file:
        lua_module_content = lua_module_file.read()

    pcw_module_content = LOCAL_MW.sub("", lua_module_content)
    pcw_module_content = LUA_REQUIRE.sub(local_to_mw_lua_require, pcw_module_content)

    return pcw_module_content


def local_file_to_module_name(file_name):
    return "Modulo:" + file_name.replace("-", "/")


def local_to_mw_lua_require(lua_require_match):
    required_module = local_file_to_module_name(lua_require_match.group(1))
    require_fn = "mw.loadData" if required_module.endswith("/data") else "require"
    return f'{require_fn}("{required_module}")'


def upload_module(module_name, module_content, edit_summary=None):
    if edit_summary is None or not pwb.input_yn(
        f'Use summary: "<<green>>{edit_summary}<<default>>"?', default=True
    ):
        edit_summary = pwb.input("Enter the edit summary")

    pcw_page = pwb.Page(pwb.Site(), module_name)

    pwb.output("Diff with current PCW version:")
    pwb.showDiff(pcw_page.text, module_content)
    if not pwb.input_yn("Proceed with upload?", default=False):
        pwb.output("Upload <<red>>aborted<<default>>")
        return

    pcw_page.text = module_content
    pcw_page.save(edit_summary)


def main(lua_module_file_name, edit_summary):
    pcw_module_content = local_file_to_module_content(lua_module_file_name)
    pcw_page_name = local_file_to_module_name(
        os.path.splitext(os.path.basename(lua_module_file_name))[0]
    )
    upload_module(pcw_page_name, pcw_module_content, edit_summary)


if __name__ == "__main__":
    main(sys.argv[1], " ".join(sys.argv[2:]))
