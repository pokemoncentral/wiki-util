#!/bin/bash

# This script prints desired aggregated
# data about models sizes. Model files
# are supposed to be on Dropbox.

# The aggregated data that can be printed
# are maximum size (out of both width and
# height) and a list of file whose width
# or height exceeds a given value

# Arguments:
#	- $1: Path to the models
#	- $2: The aggregate computation to
#		to be performed. One of:
#		- max
#		- over
#	- $3: Maximum dimension. Necessary
#		only when third argument is 'over'

# Prints the maximum dimension (height
# or width) of all models found in input
# path, ogether with the model that has
# such massive size

# Arguments:
#	- $1: Models path
function max {
	local MODELS_PATH="$1"

	local MAX_SIZE=''
	local MAX_MODEL=''

	for MODEL in $MODELS_PATH/*.gif; do
		[[ $(identify $MODEL) =~ ([0-9]+)x([0-9]+) ]]

		if [[ ${BASH_REMATCH[1]} -gt $MAX_SIZE ]]; then
			MAX_SIZE=${BASH_REMATCH[1]}
			MAX_MODEL=$MODEL
		fi

		if [[ ${BASH_REMATCH[2]} -gt $MAX_SIZE ]]; then
			MAX_SIZE=${BASH_REMATCH[2]}
			MAX_MODEL=$MODEL
		fi
	done

	echo "Max size: $MAX_SIZE; file: $MAX_MODEL"
}

# Prints every model in the provided input
# directory whose height or width is greater
# than a given value, together with such size.

# Arguments:
#	- $1: Models path
#	- $2: Maximum size
function over {
	local MODELS_PATH="$1"
	local VERGE_SIZE="$2"

	for MODEL in $MODELS_PATH/*.gif; do
		[[ $(identify $MODEL) =~ ([0-9]+)x([0-9]+) ]]

		if [[ ${BASH_REMATCH[1]} -gt $VERGE_SIZE ]]; then
			echo "Width: ${BASH_REMATCH[1]}; file: $MODEL"

		elif [[ ${BASH_REMATCH[2]} -gt $VERGE_SIZE ]]; then
			echo "Height: ${BASH_REMATCH[2]}; file: $MODEL"
		fi
	done
}

MODELS_PATH="$1"
FUNCTION="$2"
VERGE_SIZE="$3"

case $FUNCTION in
	max)
		max $MODELS_PATH
		;;
	over)
		over $MODELS_PATH $VERGE_SIZE
		;;
esac
