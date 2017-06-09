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

local intUseless = table.filter(useless, function(_, key)
	return tonumber(key)
end)
	
for ndex, data in pairs(intUseless) do
	data = table.filter(data, function(_, abbr)
		return abbr ~= 'base'
	end)

	for abbr in pairs(data.names) do
		table.insert(r.all, string.tf(ndex) .. abbr)
	end
end

--[[

Returns the ndexes plus abbreviations of
all forms of the given ndex.

--]]
r.forms = function(ndex)
	ndex = tonumber(ndex)

	local tfNdex = string.tf(ndex)
	local forms = table.keys((alts[ndex] or useless[ndex]).names)

	return table.map(forms, function(form)
		return tFndex .. formUtil.toEmptyAbbr(form)
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
