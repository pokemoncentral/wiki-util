#!/usr/bin/env bash

# This script performs some syntax fixes (both grammar and code) on Pokémon
# Central Wiki

#####################################################
#
#                   Functions
#
#####################################################

# This function executes a fix on all the pages of the wiki, never asking for
# confirmation and suppressing any output. In case of error, it logs an error
# message and exits the whole script.
#
# Arguments:
#   - $1: The name of the fix to be executed.
run_fix() {
    FIX_NAME="$1"

    python pwb.py replace -pt:1 -start:! -always -fix:"$FIX_NAME" || {
        echo >&2 "Error in fix $FIX_NAME"
        exit 1
    }

    unset FIX_NAME
}

#####################################################
#
#                   Replacements
#
#####################################################

cd "$PYWIKIBOT_DIR" || exit 1

# Grammar
run_fix 'grammar'

# Case-sensitive names
run_fix 'names-case-sensitive'

# Case-insensitive names
run_fix 'names-case-insensitive'

# Obsolete template removal
run_fix 'obsolete-templates'

