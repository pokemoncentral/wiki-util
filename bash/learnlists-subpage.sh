#!/bin/bash

TARGET=''
TMPNAME='pagetmp'

while getopts "hp:" OPTION; do
	case $OPTION in
		h)
			echo "This script moves all learnlists from a Pokémon's
page to a subpage. It's used when we get a new gen
and we need to create the subpages.

Arguments:
	- h: Show this help
	- p: Name of the page on which operate (possibly a Pokémon's)
"
			;;
		p)
			TARGET="$OPTARG"
			;;
		*) # getopts already printed an error message
			exit 1
			;;
	esac
done

if [[ -z $TARGET ]]; then
	echo No target page specified. Aborting
	exit 1
fi

TMPDIR=$(mktemp -d)
# echo $TMPDIR
python $PYWIKIBOT_DIR/pwb.py sections -simulate -local-file-path:"$TMPDIR" -page:"$TARGET" "Aumentando di [[livello]]" "Tramite [[MT]]" "Tramite [[Accoppiamento Pokémon|accoppiamento]]" "Dall'[[Insegnamosse]]" "Tramite [[evoluzione|evoluzioni]] precedenti" "Cambio di forma" "Tramite [[Pokémon evento|eventi]]"
# python $PYWIKIBOT_DIR/pwb.py sections -simulate -local-file-path:"$TMPDIR" -page:"$TARGET" "Mosse apprese"

echo "{{-start-}}" > "$TMPDIR/$TMPNAME"
cat "$TMPDIR/$TARGET" >> "$TMPDIR/$TMPNAME"
echo "[[Categoria:Apprendimento mosse Pokémon (settima generazione)]]" >> "$TMPDIR/$TMPNAME"
echo "[[en:$TARGET (Pokémon)/Generation VII learnset]]" >> "$TMPDIR/$TMPNAME"
echo "{{-stop-}}" >> "$TMPDIR/$TMPNAME"
python $PYWIKIBOT_DIR/pwb.py pagefromfile -title:"$TARGET/Mosse apprese in settima generazione" -file:"$TMPDIR/$TMPNAME" -summary:"Moving learnlists to subpage"

rm -rf "$TMPDIR"
