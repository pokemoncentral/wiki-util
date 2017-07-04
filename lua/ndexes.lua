--[[

Utility script to generate ndex lists.

This script generates list containing
ndex numbers, including alternative forms.
A list of all ndexes is ready-made.

--]]

local r = {}

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local formUtil = require('Wikilib-forms')
local genUtil = require('Wikilib-gens')
local isInGame = require('is-in-game')
local alts = require('AltForms-data')
local gendata = require('Gens-data')
local pokes = require('Poké-data')
local useless = require('UselessForms-data')

--[[

r.all contains all the ndex numbers,
formatted on three digits and including
alternative forms.

--]]
r.all = table.keys(pokes)
r.all = table.filter(r.all, string.parseInt)
r.all = table.map(r.all, function(ndex)
	return type(ndex) == 'string'
			and ndex
			or string.tf(ndex)
end)
	
for key, data in table.nonIntPairs(useless) do
	for _, abbr in ipairs(data.gamesOrder) do
        if abbr ~= 'base' then
            table.insert(r.all, string.tf(pokes[key]
                    .ndex) .. abbr)
        end
	end
end

--[[

Returns the ndexes plus abbreviations of
all forms of the given Pokémon existing
in the provided game or generation.
The Pokémon is accepted as either ndex or
name; since can be either a generation or
a game abbreviation, and defaults to the
most recent game.

--]]
r.forms = function(poke, since)
    if not since then
        local latestGenGames = gendata[gendata.latest].games
        since = latestGenGames[#latestGenGames]
    end

    local ndex = pokes[tonumber(poke) or poke:lower()].ndex

    if tonumber(since) then
        since = gendata[tonumber(since)].games[1]
    end

	local tfNdex = string.tf(ndex)
	local forms = alts[ndex] or useless[ndex]
    forms = table.filter(forms.gamesOrder, function(abbr)
            return isInGame(tfNdex ..
                    formUtil.toEmptyAbbr(abbr), since)
            end)

	return table.map(forms, function(form)
		return tfNdex .. formUtil.toEmptyAbbr(form)
	end)
end

--[[

Returns all the ndexes, including alternative
forms, of the Pokémon introduced in the first
game of a generation.

--]]
r.gen = function(gen)
	gen = tonumber(gen)

	return table.filter(r.all, function(ndex)

		--[[
			Brand new Pokémon (no form differences)
			are normally introduced only in the first
			games of a generation: hence, we only
			need to check if the Pokémon was introduced
			in the given generation.
		--]]
		if tonumber(ndex) then
			return genUtil.getGen.ndex(ndex) == gen
		end

		local dex, abbr = formUtil.getNameAbbr(ndex)
		local sinceGame = (alts[dex] or useless[dex])
				.since[abbr]
		return gendata[gen].games[1] == sinceGame
	end)
end

--[[

Returns all the ndexes of Pokémon, alternative
forms included, which where introduced
in tha passed game.

--]]
r.game = function(game)
	return table.filter(r.all, function(ndex)
		local sinceGame

		if tonumber(ndex) then
			local gen = genUtil.getGen.ndex(ndex)
			sinceGame = gendata[gen].games[1]
		else
			local dex, abbr = formUtil.getNameAbbr(ndex)
			sinceGame = (alts[dex] or useless[dex])
					.since[abbr]
		end

		return game == sinceGame
	end)
end

return r
