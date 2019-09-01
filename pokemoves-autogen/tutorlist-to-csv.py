#!/usr/bin/python3
import re
import csv

replaces = {
	"mimejr.": "mime jr.",
	"mr.mime": "mr. mime",
	"meloetta1": "meloettaD",
	"rattata1": "rattataA",
	"raticate1": "raticateA",
	"meowth1": "meowthA",
	"persian1": "persianA",
	"diglett1": "diglettA",
	"dugtrio1": "dugtrioA",
	"geodude1": "geodudeA",
	"graveler1": "gravelerA",
	"golem1": "golemA",
	"sandshrew1": "sandshrewA",
	"sandslash1": "sandslashA",
	"grimer1": "grimerA",
	"muk1": "mukA",
	"vulpix1": "vulpixA",
	"ninetales1": "ninetalesA",
	"exeggutor1": "exeggutorA",
	"marowak1": "marowakA",
	"raichu1": "raichuA",
	"basculin1": "basculinB",
	"shaymin1": "shayminC",
	u"nidoran": u"nidoran♂",
	u"nidoran": u"nidoran♀",
	u"flabébé": u"flabébé",
	"deoxys1": "deoxysA",
	"deoxys2": "deoxysD",
	"deoxys3": "deoxysV",
	"meowstic1": "meowsticF",
	"wormadam1": "wormadamSa",
	"wormadam2": "wormadamSc",
	"type:null": "tipo zero",
	u"farfetch’d": "farfetchd",
	"lycanroc1": "lycanrocN",
	"lycanroc2": "lycanrocC",
	"hoopa1": "hoopaL",
	"kyurem1": "kyuremN",
	"kyurem2": "kyuremB"
}
def convert_pokename(poke: str):
	poke = poke.lower().replace(" ", "-")
	if poke in replaces:
		return replaces[poke]
	else:
		return poke

def get_move_id(move: str):
	# 1,botta,1,1,40,35,100,0,10,2,1,,5,1,5
	with open("sourcecsv/moves.csv", "r") as movesfile:
		moves = csv.reader(movesfile)
		next(moves)
		for line in moves:
			if line[1].strip().lower() == move:
				return line[0]

def get_poke_id(poke: str):
	# 1,botta,1,1,40,35,100,0,10,2,1,,5,1,5
	with open("sourcecsv/pokemon.csv", "r") as file:
		r = csv.reader(file)
		next(r)
		for line in r:
			if line[1].strip().lower() == poke:
				return line[0]

noid = set()
with open("tutor_moves.txt", "r") as f, open("tutor_moves_usum.csv", "w") as out:
	csvw = csv.writer(out)
	move = ""
	for line in f:
		line = line.strip()
		if line == "":
			continue
		m = re.match("=== (.*) ===", line)
		if m:
			move = m.group(1).lower()
			print("Changed move: ", move)
			move_id = get_move_id(move)
			continue
		m = re.match("- (.*)", line)
		if m:
			poke = convert_pokename(m.group(1).lower())
			poke_id = get_poke_id(poke)
			if poke_id:
				# pokemon_id,version_group_id,move_id,pokemon_move_method_id,level,order
				csvw.writerow([get_poke_id(poke), 18, move_id, 3, 0, 8566])
			else:
				noid.add(poke)

for p in noid:
	print(p)
