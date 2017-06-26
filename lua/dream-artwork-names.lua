--[[

This script generates a list of Dream
World Artwork names for all Pokémon, or
those in a single generation or game or
for all the forms of a single Pokémon.

Arguments:
	- $1: specifies which Dream Artworks
        name are to be created. Can be
        one of these:
		
		- 'all': Creates Dream Artwork names
            for all Pokémon.
		- <gen number>: Creates Dream Artwork
            names for all Pokémon introduced
            in the first game of the given
			generation.
        - <Pokémon name>: Creates Dream Artwork
            names for all the alternative forms,
            base included, of the given Pokémon.
		- <game>: Creates Dream Artwork names
            for all Pokémon and alternate
			forms introduced in the passed
			game.

	- $2: output filename

--]]

local ndexes = require('ndexes')
local formUtil = require('Wikilib-forms')
local alt = require('AltForms-data')
local pokes = require('Poké-data')
local useless = require('UselessForms-data')

local source
if arg[1] == 'all' then
	source = ndexes.all

elseif pokes[arg[1]:lower()] then
    source = ndexes.forms(
            pokes[arg[1]:lower()].ndex)

elseif tonumber(arg[1]) then
	source = ndexes.gen(arg[1])

else
	source = ndexes.game(arg[1])
	
end

io.output(arg[2])

for _, ndex in pairs(source) do
    local nNdex = string.parseInt(ndex)

    local abbr, form = formUtil.getAbbr(ndex), ''
    if abbr ~= 'base' then
        local name

        -- Damn Pikachu
        if alt[nNdex] and alt[nNdex].names[abbr] then
            name = alt[nNdex].names[abbr]
        else
            name = useless[nNdex].names[abbr]
        end

        --[[
            Match stripts the first workd, such
            as 'Forma' or 'Manto'
        --]]
        form = '_' .. name:match('%s*(%S+)$')
    end

    io.write(string.interp('${ndex}${name}${form}_Dream.png\n',
        {
            ndex = string.tf(nNdex),
            name = string.fu(pokes[nNdex].name),
            form = form:gsub('%s', '_')
        })
    )
end
