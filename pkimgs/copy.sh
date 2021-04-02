#!/bin/bash

# bash copy.sh botdir: copy files from here to bot directory
# bash copy.sh here: copy files from bot directory to here
# PYWIKIBOT_DIR is imported from config file in bash folder

source ../bash/config.sh

declare -a pyfiles
pyfiles=("pkimgstools.py" "pkimgs-data.py" "pkimgs-create.py" "pkimgs-update.py")
declare -a dirs
dirs=("utils" "pokeforms" "exceptions")

if [ ! -d "$PYWIKIBOT_DIR" ]; then
    echo "Directory \"$PYWIKIBOT_DIR\" does not exist."
else
    case $1 in
        here)
            for file in "${pyfiles[@]}"; do
                file2="$PYWIKIBOT_DIR/scripts/userscripts/$file"
                if [ ! -f $file2 ]; then
                    echo "File \"$file2\" does not exist."
                else
                    cp $file2 $file
                fi
            done
            for dir in "${dirs[@]}"; do
                dir2="$PYWIKIBOT_DIR/data/$dir"
                if [ ! -d "$dir2" ]; then
                    echo "Directory \"$dir2\" does not exist."
                else
                    mkdir -p $dir
                    cp "$dir2"/*.txt ./$dir/
                fi
            done
            cp "$PYWIKIBOT_DIR/data/catlists/extra.txt" extra.txt
            ;;
        botdir)
            for file in "${pyfiles[@]}"; do
                cp "$file" "$PYWIKIBOT_DIR/scripts/userscripts/$file"
            done
            for dir in "${dirs[@]}"; do
                mkdir -p "$PYWIKIBOT_DIR/data/$dir"
                cp "$dir"/* "$PYWIKIBOT_DIR/data/$dir/"
            done
            mkdir -p "$PYWIKIBOT_DIR"/data/catlists
            cp extra.txt "$PYWIKIBOT_DIR"/data/catlists/extra.txt
            ;;
        *)
            exit 1
            ;;
    esac
fi
