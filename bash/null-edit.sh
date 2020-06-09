#!/usr/bin/env bash

# This script performs a null edit on a list of pages. Its argument are
# forwarded to the pywikibot "touch" script, so the list of pages can be
# obtained in any possible way that script can.
#
# Arguments:
#   -$@: Pywikibot touch script parameters.

#######################################
# Invoking pywikibot
#######################################

# Cd-ing into pywikibot directory, to be sure that the script works
cd "$PYWIKIBOT_DIR" || exit

python pwb.py touch "$@"

# Cd-ing back to leave no trace in the caller environment
cd - &> /dev/null || exit
