#!/usr/bin/python3
import re
import csv
import sys
import logging
import os
from typing import List, Tuple

logger = logging.getLogger("log")
logger.setLevel(logging.DEBUG)
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
	"nidoranf": "nidoran♀",
	"nidoranm": "nidoran♂",
	"mrmime": "mr. mime",
	"mimejr": "mime jr.",
	"farfetchd": "farfetchd",
	"hooh": "ho-oh",
	"porygonz": "porygon-z",
	"deoxysa": "deoxysA",
	"deoxysd": "deoxysD",
	"deoxysv": "deoxysV",
	"wormadamsa": "wormadamSa",
	"wormadamsc": "wormadamSc",
	"rotomc": "rotomC",
	"rotoml": "rotomL",
	"rotomg": "rotomG",
	"rotomv": "rotomV",
	"rotomt": "rotomT",
	"giratinao": "giratinaO",
	"shayminc": "shayminC"
}

def convert_pokename(poke: str):
	poke = poke.lower().replace(" ", "-")
	if poke in replaces:
		return replaces[poke]
	else:
		return poke

def get_move_id(move: str):
	move = move.strip().lower()
	# 1,botta,1,1,40,35,100,0,10,2,1,,5,1,5
	with open("docker-db/sourcecsv/moves.csv", "r") as movesfile:
		moves = csv.reader(movesfile)
		next(moves)
		for line in moves:
			if line[1].strip().lower() == move:
				return line[0]

def get_poke_id(poke: str):
	poke = poke.strip().lower()
	# 1,botta,1,1,40,35,100,0,10,2,1,,5,1,5
	with open("docker-db/sourcecsv/pokemon.csv", "r") as file:
		r = csv.reader(file)
		next(r)
		for line in r:
			if line[1].strip().lower() == poke:
				return line[0]

def split_moves(lines: List[str]):
	"""Return a Tuple[List[str], List[str], List[str], List[str]]
	These are lists of moves learned by level, breed, tm and tutor
	"""
	res = []
	# Level
	try:
		heading = "Learned Moves:"
		moves = lines[lines.index(heading) + 1:]
		res.append(moves)
	except ValueError:
		logger.log("This Pokémon doesn't learn any move by level")
		res.append([])
	# Egg, TM and possibly tutors (we don't have tutors data yet)
	for heading in ("Egg Moves", "TM Moves", "Tutor Moves"):
		try:
			headingcol = heading + ":"
			movesline = next(filter(lambda l: l.startswith(headingcol), lines))
			moves = movesline[len(headingcol):].split(",")
			res.append(moves)
		except StopIteration:
			res.append([])
	return tuple(res)

def parse_move_line(line: str, kind: int):
	if kind == 0: # level
		regex = "^(.*) @ (\d{1,3})$"
	elif kind == 1: # breed
		regex = "^(.*)$"
	elif kind == 2: # tm
		regex = "^TM\d{2,3} (.*)$"
	elif kind == 3:	# tutor
		regex = "^(.*)$"

	m = re.match(regex, line.strip())
	if not m:
		logger.error("Line of kind " + str(kind) + " doesn't match the regex")
		logger.error(line)
		exit(1)
	return m.groups()

def convert_kind(kind: int):
	"""
	1,level
	2,breed
	3,tutor
	4,tm
	"""
	if kind == 0:
		return 1
	elif kind == 1:
		return 2
	elif kind == 2:
		return 4
	elif kind == 3:
		return 3

def write_row_csv_pokemoves(poke_id: str, kind: int, elem: Tuple, csvw):
	if kind == 0: # level
		move = elem[0]
		level = elem[1]
	else:
		move = elem[0]
		level = 0
	move_id = get_move_id(move)
	if not move_id:
		logging.error("No ID for move " + move)
		exit(1)
	# pokemon_id,version_group_id,move_id,pokemon_move_method_id,level,order
	version_group_id = 22
	csvw.writerow([poke_id, version_group_id, move_id, convert_kind(kind), level, 0])


with open(sys.argv[1], "r") as f, open(sys.argv[2], "w") as out:
	csvw = csv.writer(out)
	pokelines = []
	move = ""
	for line in f:
		line = line.strip()
		if line == "": # Empty lines are the separators
			try:
				pokename = pokelines[0].split("-")[0].strip()
			except IndexError:
				logger.error("Can't find Pokémon name")
				logger.error(lines[0])
				exit(1)
			pokename = convert_pokename(pokename)
			poke_id = get_poke_id(pokename)
			if not poke_id:
				logger.error("No ID for Pokémon " + pokename)
				exit(1)
			logger.info(pokename)

			moves_by_kind = split_moves(pokelines)
			# logger.debug(str(moves_by_kind))
			parsed_moves = (list(map(lambda l: parse_move_line(l, i), lines))
							for i, lines in enumerate(moves_by_kind))
			# logger.debug(str(parsed_moves))
			for kind, moves in enumerate(parsed_moves):
				for move in moves:
					write_row_csv_pokemoves(poke_id, kind, move, csvw)
			pokelines = []
		else:
			pokelines.append(line)
