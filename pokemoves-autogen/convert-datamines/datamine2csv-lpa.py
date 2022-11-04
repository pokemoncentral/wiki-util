#!/usr/bin/python3
"""Convert LPA datamine to csv.

Note that the output of this script isn't intended to be added to the db, but
to be parsed directly by csv2pokemoves to create a pokemoves-data with LPA only
data.
"""

import re
import sys
import logging
import os
from typing import List, Tuple

logger = logging.getLogger("log")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_lh = logging.FileHandler('logs/' + os.path.basename(__file__) + '.log')
file_lh.setLevel(logging.DEBUG)
file_lh.setFormatter(formatter)
logger.addHandler(file_lh)

stdio_lh = logging.StreamHandler()
stdio_lh.setLevel(logging.WARNING)
stdio_lh.setFormatter(formatter)
logger.addHandler(stdio_lh)

replaces = {
	"mr.-mime": "mr. mime",
	"mr.-mime-1": "mr. mimeG",
	"mime-jr.": "mime jr.",
	"mr.-rime": "mr. rime",
	"pikachu": "pikachu",
	"pikachu-1": "pikachuO",
	"pikachu-2": "pikachuH",
	"pikachu-3": "pikachuSi",
	"pikachu-4": "pikachuU",
	"pikachu-5": "pikachuK",
	"pikachu-6": "pikachuA",
	"pikachu-7": "pikachuCo",
	"raichu": "raichu",
	"raichu-1": "raichuA",
	"darumaka": "darumaka",
	"darumaka-1": "darumakaG",
	"darmanitan": "darmanitan",
	"darmanitan-1": "darmanitanZ",
	"darmanitan-2": "darmanitanG",
	"darmanitan-3": "darmanitanGZ",
	"vulpix": "vulpix",
	"vulpix-1": "vulpixA",
	"ninetales": "ninetales",
	"ninetales-1": "ninetalesA",
	"diglett": "diglett",
	"diglett-1": "diglettA",
	"dugtrio": "dugtrio",
	"dugtrio-1": "dugtrioA",
	"meowth": "meowth",
	"meowth-1": "meowthA",
	"meowth-2": "meowthG",
	"persian": "persian",
	"persian-1": "persianA",
	"ponyta": "ponyta",
	"ponyta-1": "ponytaG",
	"rapidash": "rapidash",
	"rapidash-1": "rapidashG",
	"weezing": 'weezing',
	"weezing-1": 'weezingG',
	'corsola': 'corsola',
	'corsola-1': 'corsolaG',
	"zigzagoon": "zigzagoon",
	"zigzagoon-1": "zigzagoonG",
	"linoone": "linoone",
	"linoone-1": "linooneG",
	"stunfisk": "stunfisk",
	"stunfisk-1": "stunfiskG",
	"farfetch'd": "farfetchd",
	u"farfetch’d": "farfetchd",
	"farfetch'd-1": "farfetchdG",
	u"farfetch’d-1": "farfetchdG",
	"sirfetch'd": "sirfetchd",
	u"sirfetch’d": "sirfetchd",
	"cramorant": "cramorant",
	"cramorant-1": "cramorantT",
	"cramorant-2": "cramorantI",
	"toxtricity": "toxtricity",
	"toxtricity-1": "toxtricityB",
	"eiscue": "eiscue",
	"eiscue-1": "eiscueL",
	"indeedee": "indeedee",
	"indeedee-1": "indeedeeF",
	"morpeko": "morpeko",
	"morpeko-1": "morpekoV",
	"zacian": "zacian",
	"zacian-1": "zacianR",
	"zamazenta": "zamazenta",
	"zamazenta-1": "zamazentaR",
	"eternatus": "eternatus",
	"eternatus-1": "eternatusD",
	"shellos": "shellos",
	"gastrodon": "gastrodon",
	"cherrim": "cherrim",
	"sinistea": "sinistea",
	"sinistea-1": "sinisteaA",
	"polteageist": "polteageist",
	"polteageist-1": "polteageistA",
	"alcremie": "alcremie",
	"alcremie-1": "alcremieR",
	"alcremie-2": "alcremieMa",
	"alcremie-3": "alcremieMe",
	"alcremie-4": "alcremieL",
	"alcremie-5": "alcremieS",
	"alcremie-6": "alcremieRm",
	"alcremie-7": "alcremieCm",
	"alcremie-8": "alcremieTm",
	"mimikyu": "mimikyu",
	"mimikyu-1": "mimikyuS",
	"silvally": "silvally", # TODO silvally
	"silvally-1": "silvally",
	"silvally-2": "silvally",
	"silvally-3": "silvally",
	"silvally-4": "silvally",
	"silvally-5": "silvally",
	"silvally-6": "silvally",
	"silvally-7": "silvally",
	"silvally-8": "silvally",
	"silvally-9": "silvally",
	"silvally-10": "silvally",
	"silvally-11": "silvally",
	"silvally-12": "silvally",
	"silvally-13": "silvally",
	"silvally-14": "silvally",
	"silvally-15": "silvally",
	"silvally-16": "silvally",
	"silvally-17": "silvally",
	"type:null": "tipo zero",
	"type:-null": "tipo zero",
	"necrozma": "necrozma",
	"necrozma-1": "necrozmaV",
	"necrozma-2": "necrozmaA",
	"wishiwashi": "wishiwashi",
	"wishiwashi-1": "wishiwashiB",
	"pumpkaboo": "pumpkaboo",
	"pumpkaboo-1": "pumpkabooS",
	"pumpkaboo-2": "pumpkabooL",
	"pumpkaboo-3": "pumpkabooXL",
	"gourgeist": "gourgeist",
	"gourgeist-1": "gourgeistS",
	"gourgeist-2": "gourgeistL",
	"gourgeist-3": "gourgeistXL",
	"aegislash": "aegislash",
	"aegislash-1": "aegislashS",
	"meowstic": "meowstic",
	"meowstic-1": "meowsticF",
	"keldeo": "keldeo",
	"keldeo-1": "keldeoR",
	"kyurem": "kyurem",
	"kyurem-1": "kyuremN",
	"kyurem-2": "kyuremB",
	"yamask": "yamask",
	"yamask-1": "yamaskG",
	"basculin": "basculin",
	"basculin-1": "basculinB",
	"rotom": "rotom",
	"rotom-1": "rotomC",
	"rotom-2": "rotomL",
	"rotom-3": "rotomG",
	"rotom-4": "rotomV",
	"rotom-5": "rotomT",
	"exeggutor-1": "exeggutorA",
	"marowak-1": "marowakA",
	"sandshrew-1": "sandshrewA",
	"sandslash-1": "sandslashA",
	"slowpoke-1": "slowpokeG",
	"slowbro-2": "slowbroG",
	"slowking-1": "slowkingG",
	"lycanroc": "lycanroc",
	"lycanroc-1": "lycanrocN",
	"lycanroc-2": "lycanrocC",
	"urshifu-1": "urshifuP",
	"articuno-1": "articunoG",
	"zapdos-1": "zapdosG",
	"moltres-1": "moltresG",
	"calyrex-1": "calyrexG",
	"calyrex-2": "calyrexS",
	"giratina-1": "giratinaO",
	"tornadus-1": "tornadusT",
	"thundurus-1": "thundurusT",
	"landorus-1": "landorusT",
	"zygarde-1": "zygardeD",
	"zygarde-4": "zygardeP",
	"tapu-koko": "tapu koko",
	"tapu-lele": "tapu lele",
	"tapu-bulu": "tapu bulu",
	"tapu-fini": "tapu fini",
	"zarude-1": "zarudeP",

	"growlithe-1": "growlitheH",
	"arcanine-1": "arcanineH",
	"voltorb-1": "voltorbH",
	"electrode-1": "electrodeH",
	"typhlosion-1": "typhlosionH",
	"qwilfish-1": "qwilfishH",
	"sneasel-1": "sneaselH",
	"wormadam-1": "wormadamSa",
	"wormadam-2": "wormadamSc",
	"dialga-1": "dialgaO",
	"palkia-1": "palkiaO",
	"shaymin-1": "shayminC",
	"samurott-1": "samurottH",
	"lilligant-1": "lilligantH",
	"basculin-2": "basculinH",
	"zorua-1": "zoruaH",
	"zoroark-1": "zoroarkH",
	"braviary-1": "braviaryH",
	"sliggoo-1": "sliggooH",
	"goodra-1": "goodraH",
	"avalugg-1": "avaluggH",
	"decidueye-1": "decidueyeH",
}

def convert_pokename(poke: str):
	poke = poke.lower().replace(" ", "-")
	if poke in replaces:
		return replaces[poke]
	else:
		return poke

def split_moves(lines: List[str]):
	"""Return a Tuple[List[str], List[str]]
	These are lists of moves learned by level and tutor respectively
	"""
	res = []
	for fline in ("Level Up Moves:", "Legacy Level Up Moves:", "Legacy TMs:", "Legacy TRs:", "Move Shop:"):
		try:
			idx = lines.index(fline) + 1
			moves = []
			while idx < len(lines) and lines[idx].startswith("- "):
				moves.append(lines[idx])
				idx += 1
			res.append(moves)
		except ValueError:
			res.append([])
	# Extract only the kinds I need
	res[0], res[1] = res[0], res[4]
	return tuple(res)

def parse_move_line(line: str, kind: int):
	if kind == 0: # level
		# - [01] [00] Azione
		regex = "^- \[(\d{1,3})\] \[(\d{1,3})\] .*$"
	elif kind == 1:	# tutor
		# - Spaccaroccia
		regex = "^- (.*)$"

	m = re.match(regex, line.strip())
	if not m:
		logger.error("Line of kind {} doesn't match the regex".format(kind))
		logger.error(line)
		exit(1)
	return m.groups()

OUTPUT_LINES = [
	"|{}|||{}|{}| //", # 0 -> level
	"|{}|||{}| //", # 1 -> tutor
]

def get_learnlists(kind: int, parsed_moves: List[str]):
	"""Returns the learnlist call for the given input."""
	res = "\{\{#invoke: Learnlist/hf | levelhLPA | 8 }}\n"
	res += "\{\{#invoke: render | render | Modulo:Learnlist/entry8LPA | level | //\n"
	res += "".join(map(lambda move: OUTPUT_LINES[kind].format(move) + "\n", parsed_moves))
	res += "\}\}\n"
	res += "\{\{#invoke: Learnlist/hf | levelfLPA | 8 }}"
	return res

def all_pokes_info(filename):
	res = {}
	# with open(filename, "r") as f:
	# 	pokelines = []
	# 	move = ""
	# 	for line in f:
	# 		line = line.strip()
	# 		if line == "": # Empty lines are the separators
	# 			try:
	# 				pokename = pokelines[0].split(" - ")[0].strip()
	# 			except IndexError:
	# 				logger.error("Can't find Pokémon name")
	# 				logger.error(pokelines[0])
	# 				exit(1)
	# 			pokename = convert_pokename(pokename)
	# 			if re.search("-\d+$", pokename):
	# 				logger.warning("{} name ends in \"-number\". This may point to a missing replacement".format(pokename))
	# 			logger.info(pokename)

	# 			moves_by_kind = split_moves(pokelines)
	# 			parsed_moves = (list(map(lambda l: parse_move_line(l, i), lines))
	# 							for i, lines in enumerate(moves_by_kind))
	# 			logger.debug(str(list(parsed_moves)))
	# 			res[pokename] = parsed_moves
	# 			# for kind, moves in enumerate(parsed_moves):
	# 			# 	for move in moves:
	# 			# 		write_row_csv_pokemoves(poke_id, kind, move, csvw)
	# 			pokelines = []
	# 		else:
	# 			pokelines.append(line)
	# return res
	with open(filename, "r") as f, open("/tmp/massaggiato.txt", "w") as outfile:
		pokelines = []
		pokename = False
		move = ""
		for line in f:
			line = line.strip()
			if line == "======":
				if not pokename:
					if not len(pokelines) == 1:
						logger.error("More than one line when expecting the Pokémon name")
						logger.error(str(pokelines))
						exit(1)
					m = re.match("\d{3,4} \- (.*) \(Stage\: \d\)", pokelines[0])
					if not m:
						logger.error("Pokémon name line doesn't match the regex")
						logger.error(pokelines[0])
						exit(1)
					pokename = m.group(1)
					# pokename = convert_pokename(m.group(1))
					pokelines = []
				else:
					if pokelines[0] != "Present: No":
						# Pokémon in the game
						outfile.write(pokename + "\n")
						# if re.search("-\d+$", pokename):
						# 	logger.warning("{} name ends in \"-number\". This may point to a missing replacement".format(pokename))
						# logger.info(pokename)
						moves_by_kind = split_moves(pokelines)
						outfile.write("Level:\n")
						for line in moves_by_kind[0]:
							outfile.write(line + "\n")
						outfile.write("Move Shop:\n")
						for line in moves_by_kind[1]:
							outfile.write(line + "\n")
						outfile.write("\n")
						# parsed_moves = (list(map(lambda l: parse_move_line(l, i), lines))
						# 				for i, lines in enumerate(moves_by_kind))
						# logger.debug(str(list(parsed_moves)))
						# res[pokename] = parsed_moves
					pokelines = []
					pokename = False
			else:
				pokelines.append(line)
	return res


if __name__ == "__main__":
	all_info = all_pokes_info(sys.argv[1])