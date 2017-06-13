--[[

This scripts renames models from PkParaiso
to Pokémon Central wiki conventions, provided
the necessary information.

Arguments
	- $1: Filename
	- $2: Variant. One of:
		- shiny
		- back
		- back_shiny
		- normal
	- $3: Sex. One of:
		- m
		- f
	- $4: Game. One of:
		- xy
		- oras
		- roza
		- sm
		- sl
	- $5: Flag, determines the output type.
		If set, and different from 'false',
		returns the name to the caller;
		otherwise, prints it to standard
		output. Default is to print.
--]]

local txt = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local poke = require('Poké-data')
local alts = require('AltForms-data')
local data = require('Wikilib-data')
local useless = require('UselessForms-data')

local mw = require('mw')

local pcwGames = {
	oras = 'roza',
	sm = 'sl'
}

local variants = {
	shiny = 'sh',
	back = 'd',
	back_shiny = 'dsh',
	normal = ''
}

--[[

Abbreviations are fetched from data
modules to allow some degree of flexibility

--]]
local getAbbr = function(poke, extended)
	return (alts[poke] or useless[poke]).ext[extended]
end

--[[

In case of collisions in alternative
form names, a table with different
entries for each Pokémon is in place.

--]]
local abbr = {
	cosplay = getAbbr('pikachu', 'cosplay'),
	kantocap = 'Kn',
	hoenncap = 'H',
	sinnohcap = 'Si',
	unovacap = 'U',
	kaloscap = 'Kl',
	alolacap = 'A',
	bravo = getAbbr('unown', 'B'),
	charlie = getAbbr('unown', 'C'),
	delta = getAbbr('unown', 'D'),
	echo = getAbbr('unown', 'E'),
	exclamation = getAbbr('unown', '!'),
	foxtrot = getAbbr('unown', 'F'),
	golf = getAbbr('unown', 'G'),
	hotel = getAbbr('unown', 'H'),
	india = getAbbr('unown', 'I'),
	interrogation = getAbbr('unown', '?'),
	juliet = getAbbr('unown', 'J'),
	kilo = getAbbr('unown', 'K'),
	lima = getAbbr('unown', 'L'),
	mike = getAbbr('unown', 'M'),
	november = getAbbr('unown', 'N'),
	oscar = getAbbr('unown', 'O'),
	papa = getAbbr('unown', 'P'),
	quebec = getAbbr('unown', 'Q'),
	romeo = getAbbr('unown', 'R'),
	sierra = getAbbr('unown', 'S'),
	tango = getAbbr('unown', 'T'),
	uniform = getAbbr('unown', 'U'),
	victor = getAbbr('unown', 'V'),
	whiskey = getAbbr('unown', 'W'),
	xray = getAbbr('unown', 'X'),
	yankee = getAbbr('unown', 'Y'),
	zulu = getAbbr('unown', 'Z'),
	rainy = getAbbr('castform', 'pioggia'),
	sunny = getAbbr('castform', 'sole'),
	snowy = getAbbr('castform', 'neve'),
	attack = getAbbr('deoxys', 'attacco'),
	defense = getAbbr('deoxys', 'difesa'),
	speed = getAbbr('deoxys', 'velocità'),
	sandy = getAbbr('burmy', 'sabbia'),
	trash = getAbbr('burmy', 'scarti'),
	sunshine = getAbbr('cherrim', 'splendore'),
	east = getAbbr('shellos', 'est'),
	fan = getAbbr('rotom', 'vortice'),
	frost = getAbbr('rotom', 'gelo'),
	heat = getAbbr('rotom', 'calore'),
	mow = getAbbr('rotom', 'taglio'),
	wash = getAbbr('rotom', 'lavaggio'),
	origin = getAbbr('giratina', 'originale'),
	sky = getAbbr('shaymin', 'cielo'),
	blue = {
		basculin = getAbbr('basculin', 'lineablu'),
		['flabébé'] = getAbbr('flabébé', 'blu'),
		floette = getAbbr('floette', 'blu'),
		florges = getAbbr('florges', 'blu')
	},
	zen = getAbbr('darmanitan', 'zen'),
	autumn = getAbbr('deerling', 'autunno'),
	summer = getAbbr('deerling', 'estate'),
	winter = getAbbr('deerling', 'inverno'),
	therian = getAbbr('thundurus', 'totem'),
	black = getAbbr('kyurem', 'nero'),
	white = {
		kyurem = getAbbr('kyurem', 'bianco'),
		['flabébé'] = getAbbr('flabébé', 'bianco'),
		floette = getAbbr('floette', 'bianco'),
		florges = getAbbr('florges', 'bianco')
	},
	resolute = getAbbr('keldeo', 'risoluta'),
	pirouette = getAbbr('meloetta', 'danza'),
	archipelago = getAbbr('vivillon', 'arcipelago'),
	continental = getAbbr('vivillon', 'continentale'),
	elegant = getAbbr('vivillon', 'eleganza'),
	garden = getAbbr('vivillon', 'prato'),
	highplains = getAbbr('vivillon', 'deserto'),
	jungle = getAbbr('vivillon', 'giungla'),
	marine = getAbbr('vivillon', 'marino'),
	meadow = getAbbr('vivillon', 'giardinfiore'),
	modern = getAbbr('vivillon', 'trendy'),
	monsoon = getAbbr('vivillon', 'pluviale'),
	ocean = getAbbr('vivillon', 'oceanico'),
	polar = getAbbr('vivillon', 'nordico'),
	river = getAbbr('vivillon', 'fluviale'),
	sandstorm = getAbbr('vivillon', 'sabbia'),
	savannah = getAbbr('vivillon', 'savana'),
	sun = getAbbr('vivillon', 'solare'),
	tundra = getAbbr('vivillon', 'manto di neve'),
	fancy = getAbbr('vivillon', 'sbarazzino'),
	pokeball = getAbbr('vivillon', 'poké ball'),
	orange = getAbbr('floette', 'arancione'),
	yellow = getAbbr('floette', 'giallo'),
	-- eternal = getAbbr('floette', 'blu'),
	blade = getAbbr('aegislash', 'spada'),
	small = getAbbr('pumpkaboo', 'mini'),
	large = getAbbr('pumpkaboo', 'grande'),
	big = getAbbr('pumpkaboo', 'maxi'),
	active = getAbbr('xerneas', 'attivo'),
	mega = getAbbr('venusaur', 'mega'),
	megax = getAbbr('charizard', 'megax'),
	megay = getAbbr('charizard', 'megay'),
	primal = getAbbr('kyogre', 'archeo'),
	['10'] = {
		zygarde = getAbbr('zygarde', 'dieci')
	},
	complete = getAbbr('zygarde', 'perfetto'),
	unbound = getAbbr('hoopa', 'libero'),
	alola = getAbbr('rattata', 'alola'),
	midnight = getAbbr('lycanroc', 'notte'),
	pompom = getAbbr('oricorio', 'cheerdance'),
	pau = getAbbr('oricorio', 'hula'),
	sensu = getAbbr('oricorio', 'buyo'),
	school = getAbbr('wishiwashi', 'banco'),
	steel = getAbbr('arceus', 'acciaio'),
	grass = getAbbr('arceus', 'erba'),
	bug = getAbbr('arceus', 'coleottero'),
	dark = getAbbr('arceus', 'buio'),
	fire = getAbbr('arceus', 'fuoco'),
	dragon = getAbbr('arceus', 'drago'),
	ice = getAbbr('arceus', 'ghiaccio'),
	flying = getAbbr('arceus', 'volante'),
	fighting = getAbbr('arceus', 'lotta'),
	psychic = getAbbr('arceus', 'psico'),
	ghost = getAbbr('arceus', 'spettro'),
	rock = getAbbr('arceus', 'roccia'),
	ground = getAbbr('arceus', 'terra'),
	poison = getAbbr('arceus', 'veleno'),
	fairy = getAbbr('arceus', 'folletto'),
	water = getAbbr('arceus', 'acqua'),
	electric = getAbbr('arceus', 'elettro'),
	red = getAbbr('minior', 'rosso'),
	green = getAbbr('minior', 'verde'),
	indigo = getAbbr('minior', 'indaco'),
	violet = getAbbr('minior', 'violetto'),
	broken = getAbbr('mimikyu', 'smascherata'),
	['2'] = {
		mimikyu = getAbbr('mimikyu', 'smascherata')
	}
}

-- Match strips away any extension
local splits = mw.text.split(arg[1]:match('(.+)%..+$'),
		'-', true)

local move, form = '', ''
local name = {splits[1]}

if #splits > 1 then

	--[[
		Pieces are matched from the end.
		They are first checked against
		move/form, and if both fail then
		the piece is considered part of
		the Pokémon name.
	--]]
	for k = #splits, 2, -1 do
		local piece = splits[k]
		local formOrMove = false

		if tonumber(piece) then
			move = piece
			formOrMove = true
		end

		if abbr[piece] then
			form = piece
			formOrMove = true
		end

		if not formOrMove then
			table.insert(name, 2, piece)
		end
	end
end

name = table.concat(name, '-')
-- Replace with table lookup if necessary
if name == 'typenull' then
	name = 'tipo zero'
end

local ndex = poke[name].ndex

if move ~= '' and form ~= ''
		and move == form
then
	--[[
		If form and move were found
		and are the same, this means
		that we have a numerical form
		name: if there is an abbreviation
		for the Pokémon name, then it
		is regarded as a form, otherwise
		as a move
	--]]
	if abbr[form][name] then	
		move = ''
		form = abbr[form][name]
	else
		move = '-' .. move
		form = ''
	end
else
	if form ~= '' then
		form = type(form) == 'table'
				and abbr[form][name]
				or abbr[form]
	end

	if move ~= '' then
		move = '-' .. move
	end
end

local spr = string.interp(
	'Spr${game}${sex}${var}${ndex}${form}${move}.gif',
	{
		game = pcwGames[arg[4]] or arg[4],
		var = variants[arg[2]],
		sex = table.search(data.onlyFemales, ndex)
				and 'f' or arg[3],
		ndex = string.tf(ndex),
		form = form,
		move = move
	}
)

if arg[5] == 'false' or arg[5] then
	return spr
else
	print(spr)
end
