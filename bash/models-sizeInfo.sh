#!/bin/bash

# Arguments
# $1: size --> max sized file; over -->

function size {

for k in ~/Dropbox/Wiki/Sprite/Modelli_xy/$1/*.gif
do
	[[ $(identify $k) =~ ([0-9]+)x([0-9]+) ]]
	if [[ ${BASH_REMATCH[1]} -gt $max ]]; then
		max=${BASH_REMATCH[1]}
		file=$k
	fi
	if [[ ${BASH_REMATCH[2]} -gt $max ]]; then
		max=${BASH_REMATCH[2]}
		file=$k
	fi
done

echo "Max size: $max; file: $file"
}

function over {

for k in ~/Dropbox/Wiki/Sprite/Modelli_xy/$1/*.gif
do
	[[ $(identify $k) =~ ([0-9]+)x([0-9]+) ]]
	if [[ ${BASH_REMATCH[1]} -gt $2 ]]; then
		echo "Width: ${BASH_REMATCH[1]}; file: $k" >> over.txt
	else
		if [[ ${BASH_REMATCH[2]} -gt $2 ]]; then
			echo "Height: ${BASH_REMATCH[2]}; file: $k" >> over.txt
		fi
	fi
done
}

case $1 in
	size)
		size $2
		;;
	over)
		if [[ $2 == '' ]]; then
			over '' $3
		else
			over $2 $3
		fi
		;;
esac
