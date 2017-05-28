#!/bin/bash

# This script returns the actual file type
# in lowercase, regardless of extensions

# Arguments:
#	- $1: Source file

file -b "$1" | awk '{ print tolower($1) }'
