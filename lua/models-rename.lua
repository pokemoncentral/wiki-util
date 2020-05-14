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
-- local alts = require('AltForms-data')
local data = require('Wikilib-data')
-- local useless = require('UselessForms-data')
local alts = require('Wikilib-forms').allFormsData()

local mw = require('mw')

local pcwGames = {
	oras = 'roza',
	sm = 'sl',
	swsh = 'spsc',
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
	return alts[poke].ext[extended]
end

--[[

In case of collisions in alternative
form names, a table with different
entries for each Pokémon is in place.

--]]
local abbr = {
    f = '',
	cosplay = getAbbr('pikachu', 'cosplay'),
	belle = getAbbr('pikachu', 'damigella'),
	rockstar = getAbbr('pikachu', 'rockstar'),
	popstar = getAbbr('pikachu', 'confetto'),
	phd = getAbbr('pikachu', 'scienziata'),
	libre = getAbbr('pikachu', 'wrestler'),
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
		florges = getAbbr('florges', 'blu'),
		minior = getAbbr('minior', 'azzurro'),
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
    douse = getAbbr('genesect', 'idromodulo'),
    burn = getAbbr('genesect', 'piromodulo'),
    chill = getAbbr('genesect', 'gelomodulo'),
    shock = getAbbr('genesect', 'voltmodulo'),
	ash = getAbbr('greninja', 'ash'),
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
	orange = {
		floette = getAbbr('floette', 'arancione'),
		florges = getAbbr('floette', 'arancione'),
		['flabébé'] = getAbbr('floette', 'arancione'),
		minior = getAbbr('minior', 'arancione'),
	},
	yellow = {
		floette = getAbbr('floette', 'giallo'),
		florges = getAbbr('floette', 'giallo'),
		['flabébé'] = getAbbr('floette', 'giallo'),
		minior = getAbbr('minior', 'giallo'),
	},
	eternal = 'E',
	blade = getAbbr('aegislash', 'spada'),
	small = getAbbr('pumpkaboo', 'mini'),
	large = getAbbr('pumpkaboo', 'grande'),
	big = getAbbr('pumpkaboo', 'maxi'),
	super = getAbbr('pumpkaboo', 'maxi'),
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
	},
	galar = getAbbr('corsola', 'galar'),
	["galarzen"] = getAbbr('darmanitan', 'galar zen'),
	lowkey = getAbbr('toxtricity', 'basso'),
	gulping = getAbbr('cramorant', 'inghiottitutto'),
	gorging = getAbbr('cramorant', 'inghiottintero'),
	noice = getAbbr('eiscue', 'liquefaccia'),
	hangry = getAbbr('morpeko', 'panciavuota'),
	crowned = getAbbr('zacian', 're'),
	eternamax = getAbbr('eternatus', 'dynamax'),
	gigantamax = getAbbr('corviknight', 'gigamax'),
	-- Alcremie
	["caramel£swirl"] = getAbbr('alcremie', 'caramelmix'),
	["lemon£cream"] = getAbbr('alcremie', 'lattelimone'),
	["matcha£cream"] = getAbbr('alcremie', 'lattematcha'),
	["mint£cream"] = getAbbr('alcremie', 'lattementa'),
	["rainbow£swirl"] = getAbbr('alcremie', 'triplomix'),
	["ruby£cream"] = getAbbr('alcremie', 'latterosa'),
	["ruby£swirl"] = getAbbr('alcremie', 'rosamix'),
	["salted£cream"] = getAbbr('alcremie', 'lattesale'),
	["vanilla£cream"] = '',
	["berry"] = "B",
	["clover"] = "Fg",
	["flower"] = "Fi",
	["love"] = "C",
	["ribbon"] = "Fo",
	["star"] = "S",
	["strawberry"] = "Fr",

	["caramel£swirlberry"] = getAbbr('alcremie', 'caramelmix') .. "B",
	["caramel£swirlclover"] = getAbbr('alcremie', 'caramelmix') .. "Fg",
	["caramel£swirlflower"] = getAbbr('alcremie', 'caramelmix') .. "Fi",
	["caramel£swirllove"] = getAbbr('alcremie', 'caramelmix') .. "C",
	["caramel£swirlribbon"] = getAbbr('alcremie', 'caramelmix') .. "Fo",
	["caramel£swirlstar"] = getAbbr('alcremie', 'caramelmix') .. "S",
	["caramel£swirlstrawberry"] = getAbbr('alcremie', 'caramelmix') .. "Fr",

	["lemon£creamberry"] = getAbbr('alcremie', 'lattelimone') .. "B",
	["lemon£creamclover"] = getAbbr('alcremie', 'lattelimone') .. "Fg",
	["lemon£creamflower"] = getAbbr('alcremie', 'lattelimone') .. "Fi",
	["lemon£creamlove"] = getAbbr('alcremie', 'lattelimone') .. "C",
	["lemon£creamribbon"] = getAbbr('alcremie', 'lattelimone') .. "Fo",
	["lemon£creamstar"] = getAbbr('alcremie', 'lattelimone') .. "S",
	["lemon£creamstrawberry"] = getAbbr('alcremie', 'lattelimone') .. "Fr",

	["matcha£creamberry"] = getAbbr('alcremie', 'lattematcha') .. "B",
	["matcha£creamclover"] = getAbbr('alcremie', 'lattematcha') .. "Fg",
	["matcha£creamflower"] = getAbbr('alcremie', 'lattematcha') .. "Fi",
	["matcha£creamlove"] = getAbbr('alcremie', 'lattematcha') .. "C",
	["matcha£creamribbon"] = getAbbr('alcremie', 'lattematcha') .. "Fo",
	["matcha£creamstar"] = getAbbr('alcremie', 'lattematcha') .. "S",
	["matcha£creamstrawberry"] = getAbbr('alcremie', 'lattematcha') .. "Fr",

	["mint£creamberry"] = getAbbr('alcremie', 'lattementa') .. "B",
	["mint£creamclover"] = getAbbr('alcremie', 'lattementa') .. "Fg",
	["mint£creamflower"] = getAbbr('alcremie', 'lattementa') .. "Fi",
	["mint£creamlove"] = getAbbr('alcremie', 'lattementa') .. "C",
	["mint£creamribbon"] = getAbbr('alcremie', 'lattementa') .. "Fo",
	["mint£creamstar"] = getAbbr('alcremie', 'lattementa') .. "S",
	["mint£creamstrawberry"] = getAbbr('alcremie', 'lattementa') .. "Fr",

	["rainbow£swirlberry"] = getAbbr('alcremie', 'triplomix') .. "B",
	["rainbow£swirlclover"] = getAbbr('alcremie', 'triplomix') .. "Fg",
	["rainbow£swirlflower"] = getAbbr('alcremie', 'triplomix') .. "Fi",
	["rainbow£swirllove"] = getAbbr('alcremie', 'triplomix') .. "C",
	["rainbow£swirlribbon"] = getAbbr('alcremie', 'triplomix') .. "Fo",
	["rainbow£swirlstar"] = getAbbr('alcremie', 'triplomix') .. "S",
	["rainbow£swirlstrawberry"] = getAbbr('alcremie', 'triplomix') .. "Fr",

	["ruby£creamberry"] = getAbbr('alcremie', 'latterosa') .. "B",
	["ruby£creamclover"] = getAbbr('alcremie', 'latterosa') .. "Fg",
	["ruby£creamflower"] = getAbbr('alcremie', 'latterosa') .. "Fi",
	["ruby£creamlove"] = getAbbr('alcremie', 'latterosa') .. "C",
	["ruby£creamribbon"] = getAbbr('alcremie', 'latterosa') .. "Fo",
	["ruby£creamstar"] = getAbbr('alcremie', 'latterosa') .. "S",
	["ruby£creamstrawberry"] = getAbbr('alcremie', 'latterosa') .. "Fr",

	["ruby£swirlberry"] = getAbbr('alcremie', 'rosamix') .. "B",
	["ruby£swirlclover"] = getAbbr('alcremie', 'rosamix') .. "Fg",
	["ruby£swirlflower"] = getAbbr('alcremie', 'rosamix') .. "Fi",
	["ruby£swirllove"] = getAbbr('alcremie', 'rosamix') .. "C",
	["ruby£swirlribbon"] = getAbbr('alcremie', 'rosamix') .. "Fo",
	["ruby£swirlstar"] = getAbbr('alcremie', 'rosamix') .. "S",
	["ruby£swirlstrawberry"] = getAbbr('alcremie', 'rosamix') .. "Fr",

	["salted£creamberry"] = getAbbr('alcremie', 'lattesale') .. "B",
	["salted£creamclover"] = getAbbr('alcremie', 'lattesale') .. "Fg",
	["salted£creamflower"] = getAbbr('alcremie', 'lattesale') .. "Fi",
	["salted£creamlove"] = getAbbr('alcremie', 'lattesale') .. "C",
	["salted£creamribbon"] = getAbbr('alcremie', 'lattesale') .. "Fo",
	["salted£creamstar"] = getAbbr('alcremie', 'lattesale') .. "S",
	["salted£creamstrawberry"] = getAbbr('alcremie', 'lattesale') .. "Fr",

	["vanilla£creamberry"] = 'V' .. "B",
	["vanilla£creamclover"] = 'V' .. "Fg",
	["vanilla£creamflower"] = 'V' .. "Fi",
	["vanilla£creamlove"] = 'V' .. "C",
	["vanilla£creamribbon"] = 'V' .. "Fo",
	["vanilla£creamstar"] = 'V' .. "S",
	["vanilla£creamstrawberry"] = 'V' .. "Fr",
}

--[[

Some abbr contain dashes, and this doesn't work with
the split. They are listed in this table, so that they
can be replaced with a $ sign.

--]]
local dashedStrings = {
	"type-null", "caramel-swirl", "lemon-cream", "matcha-cream",
	"mint-cream", "rainbow-swirl", "ruby-cream", "ruby-swirl", "salted-cream",
	"vanilla-cream",
}

--[[
	Some Pkparaiso names are not
	found directly in Poké-data
--]]
local trueNames = {
	['nidoran f'] = 'nidoran♀',
	['nidoran m'] = 'nidoran♂',
	farfetchd = "farfetch'd",
	['mime jr'] = 'mime jr.',
	['flabebe'] = 'flabébé',
	typenull = 'tipo zero',
	['type£null'] = 'tipo zero',
	tapukoko = 'tapu koko',
	tapulele = 'tapu lele',
	tapubulu = 'tapu bulu',
	tapufini = 'tapu fini',
	sirfetchd = "sirfetch'd",
}

local modelname = arg[1]

-- Replaces dashedAbbr
for _, s in pairs(dashedStrings) do
	modelname = modelname:gsub(s:gsub("%-", "%%-"), s:gsub("%-", "£"))
end

-- Match strips away any extension
local splits = mw.text.split(modelname:match('(.+)%..+$'),
		'-', true)

local move, form = '', {}
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
			table.insert(form, 1, piece)
			formOrMove = true
		end

		if not formOrMove then
			table.insert(name, 2, piece)
		end
	end
end

form = table.concat(form)
name = table.concat(name, '-'):gsub('_', ' ')
name = trueNames[name] or name

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
		form = type(abbr[form]) == 'table'
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
