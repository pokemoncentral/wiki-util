#!/bin/bash

. $HOME/.bash_envvars

# This script creates redirects for artworks of
# forms that lack a Sugimori version but have
# a Dream World one.

# Arguments
#	-o filename: Oputput file name
#	-s summary: Summary used when uploading
#	-p: Set the putthrottle to 1
#	-t: Only creates output file, doesn't upload

OUTFILE=forms.txt
SUMMARY='Redirect agli Artwork Dream World per le forme alternative'
PT=''
UPLOAD=true

while getopts 'o:s:pt' OPTION; do
	case $OPTION in
		o)
			OUTFILE=$OPTARG
			;;
		s)
			SUMMARY=$OPTARG
			;;
		p)
			PT='-putthrottle:1'
			;;
		t)
			UPLOAD=false
			;;
		*)
			echo Unrecognized option
			exit 1
			;;
	esac
done

declare names
names[649]=Genesect

forms=('Voltmodulo' 'Idromodulo' 'Piromodulo' 'Gelomodulo')

:> $OUTFILE

for POKE in "${!names[@]}"; do
	NAME=${names[$POKE]}
	for FORM in "${forms[@]}"; do
		echo -e "{{-start-}}\n'''File:Artwork$POKE-$FORM.png'''\n#RINVIA[[File:$POKE$NAME $FORM Dream.png]]\n{{-stop-}}" >> $OUTFILE
	done
done

if $UPLOAD; then
	python $PYWIKIBOT_DIR/pwb.py pagefromfile $PT -notitle -force -summary:"$SUMMARY" -file:$OUTFILE
	rm $OUTFILE
fi
