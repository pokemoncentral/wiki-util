#!/bin/bash

# Arguments
# None

function page {
	sourceGame=$1
	sourceNum=$2
	destGame=$3
	destNum=$4
	echo  {{-start-}} >> redirects.txt
	# echo "'''File:Spr$destGame$destNum.gif'''" >> redirects.txt
	echo "'''File:$destGame$destNum.png'''" >> redirects.txt
	# echo "#RINVIA[[File:Spr$sourceGame$sourceNum.png]]" >> redirects.txt
	echo "#RINVIA[[File:$sourceGame$sourceNum.png]]" >> redirects.txt
	echo {{-stop-}} >> redirects.txt
}

females=(029 030 031 113 115 124 238 241 242 314 380 413 416 440 478 488 548 549
	629 630 669 670 671 115 380 413 413)

alsoFemales=(003 012 019 020 025 041 042 044 045 064 065 084 085 097 111 112 118 119 123 129 130
	154 165 166 172 178 185 186 190 194 195 198 202 203 207 208 212 214 215 217 221
	224 229 232 256 257 267 269 272 274 275 307 308 315 316 317 322 323 332 350 369
	396 397 398 399 400 401 402 403 404 405 407 415 417 418 419 424 443 444 445 449
	450 453 454 456 457 459 460 461 464 465 473)

males=(493 144 482 343 374 437 436 703 251 344 638 615 491 386 483 719 132 101 244 649 487 622 623 382 383 250 285 647 600 599 646 249 081 082 462 490 648 481 376 375 151 150 146 484 489 137 474 233 243 384 378 486 377 379 643 479 492 292 338 121 120 245 639 201 480 494 640 100 716 717 145 718 720 644 601 032 033 034 106 107 128 236 237 313 381 414 475 538 539 627 628 641 642 645)

# for ndex in {001..720}; do
	# onlyFemale=$([[ ${females[*]} =~ $ndex ]] && echo true || echo false)
	# alsoFemale=$([[ ${alsoFemales[*]} =~ $ndex ]] && echo true || echo false)
	# onlyMale=$([[ ${males[*]} =~ $ndex ]] && echo true || echo false)
	# for variant in {'',sh,d,dsh}; do
		# if $onlyFemale; then
			# page xyf$variant $ndex rozaf$variant $ndex
		# else
			# if $onlyMale; then
				# page xym$variant $ndex rozam$variant $ndex
			# else
				# page xym$variant $ndex rozam$variant $ndex
				# if $alsoFemale; then
					# page xyf$variant $ndex rozaf$variant $ndex
				# else
					# page xym$variant $ndex rozaf$variant $ndex
				# fi
			# fi
		# fi
	# done
# done

for ndex in f025Cs m015M m018M m080M m208M m254M m260M m302M m319M m323M m334M m362M m373M m376M m382A m383A m384M m428M m475M m531M m719M; do
	page 'roza' $ndex '' ${ndex:1}
done
