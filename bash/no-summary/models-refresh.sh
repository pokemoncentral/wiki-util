#!/bin/bash

# Arguments
# -h [yes, no]: halts the system once done

cd $(dirname $0)
bash XYModels-download.sh normal oras
bash XYModels-download.sh shiny oras
bash XYModels-download.sh back oras
bash XYModels-download.sh back_shiny oras

while getopts "h:" opt; do
	if [[ $OPTARG =~ y ]]; then
		halt -p
	fi
done
