#!/bin/bash

# Ths script processes all images in a directory.
# The images are squared adding transparent pixels;
# the new size is the biggest one if it is greater
# than the provided one, else this very last

# Arguments
#	- $1: Directory images to be resized are in
#	- $2: Output size of images

DIR="$1"
MIN_SIZE=$2

for IMG in "$DIR"/*; do
	
	# Getting the biggest out of two sides and minumim size

	[[ $(identify "$IMG") =~ ([0-9]+)x([0-9]+) ]]
	if [[ ${BASH_REMATCH[1]} -gt ${BASH_REMATCH[2]} ]]; then
		SIZE=${BASH_REMATCH[1]}
	else
		SIZE=${BASH_REMATCH[2]}
	fi
	[[ $SIZE -lt $MIN_SIZE ]] && SIZE=$MIN_SIZE

	# Optimized gifs yeld strange results, need to be unoptimized

	EXT=${IMG##*.}
	EXT=${EXT,,}
	[[ $EXT == 'gif' ]] && gifsicle -b --unoptimize "$IMG"

	# Actually resizing

	mogrify -background transparent -gravity center -extent ${SIZE}x${SIZE} -quality 100 "$IMG"

	# Optimizing gifs back

	[[ $EXT == 'gif' ]] && gifsicle -b -O3 "$IMG"

	echo $(basename "$IMG") resized
done
