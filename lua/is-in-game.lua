--[[

This function returns wether the
passed Pokémon, form included,
exists in the given game.

--]]

local tab = require('Wikilib-tables')
local formUtil = require('Wikilib-forms')
local gens = require('Wikilib-gens')
local alts = require('AltForms-data')
local data = require('Wikilib-data')
local pokes = require('Poké-data')
local useless = require('UselessForms-data')

return function(poke, game)
	local ndex = pokes[tonumber(poke) or poke].ndex
	local abbr = formUtil.getAbbr(poke)

	if abbr == 'base' then
		return gens.getGen.game(game)
				>= gens.getGen.ndex(ndex)
	end

	local alt = alts[ndex] or useless[ndex]
	local sinceOrd = table.search(data.gamesChron,
			alt.since[abbr])
	local gameOrd = table.search(data.gamesChron,
			game)

	return gameOrd >= sinceOrd
end
