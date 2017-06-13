#!/bin/bash

. ./config.sh

SCRIPT="$1"

shift 1

bash "$SCRIPT" "$@"
