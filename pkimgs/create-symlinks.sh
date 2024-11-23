#!/bin/bash

# get script directory
script_dir="$(dirname "$(realpath $0)")"
# source config to get Pywikibot directory
source "$script_dir"/../bash/config.sh
# create symlinks of all Python scripts
for file in $(ls -f "$script_dir"/*.py); do
    file_name="$(basename "$file")"
    ln -sf "$file" "$PYWIKIBOT_DIR/scripts/userscripts/$file_name"
done
# create symlink of extras file
mkdir -p "$PYWIKIBOT_DIR/data/pokepages-catlists"
ls -sf "$script_dir/extra.txt" "$PYWIKIBOT_DIR/data/pokepages-catlists/extra.txt"
# create symlinks of directories
for dir in $(ls -d "$script_dir"/pokepages-*); do
    dir_name="$(basename "$dir")"
    ln -sf "$dir" "$PYWIKIBOT_DIR/data/$dir_name"
done
