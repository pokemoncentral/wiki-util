#!/usr/bin/env bash

#######################################
# Initial setup
#######################################

PARENT_DIR="$(dirname "${BASH_SOURCE[0]}" | xargs readlink -f)"
source "$PARENT_DIR/config.sh"

#######################################
# Input processing
#######################################

SCRIPT="$PARENT_DIR/$(basename "$1")"
shift 1

[ ! -f "$SCRIPT" ] && {
    echo >&2 "Script not found: $1"
    exit 1
}

#######################################
# Invoking script
#######################################

# Cd-ing into parent directory so that the executed scripts can assume to be
# running there
cd "$PARENT_DIR" || exit

bash "$SCRIPT" "$@"

# Cd-ing back so as not to pollute the caller's environment
cd - &> /dev/null || exit
