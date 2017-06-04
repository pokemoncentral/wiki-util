--[[

This script creates redirects file for sprites
from one game to another.

Arguments
	- $1: source game
	- $2: target game
	- $3: output file

--]]

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local isInGame = require('is-in-game')
local makeDict = require('dict-page')
local data = require('Wikilib-data')
local ndexes = require('ndexes')

local makeRedirect = function(source, dest, sex, ndex)
	local pages = {}

	for _, variant in pairs({'', 'd', 'sh', 'dsh'}) do
		local title = string.interp(
			'File:Spr${game}${sex}${var}${ndex}.gif',
			{
				game = dest,
				sex = sex,
				var = variant,
				ndex = ndex
			}
		)
		local body = string.interp(
			'#RINVIA[[File:Spr${game}${sex}${var}${ndex}.gif]]',
			{
				game = source,
				sex = sex,
				var = variant,
				ndex = ndex
			}
		)

		table.insert(pages, makeDict(title, body))
	end

	return table.concat(pages)
end

local source, dest = arg[1], arg[2]

io.output(arg[3])

for _, ndex in pairs(ndexes.all) do
	if isInGame(ndex, source) then
		local nNdex = string.parseInt(ndex)
		
		local sex = 'm'
		if table.search(data.onlyFemales, nNdex) then
			sex = 'f'
		end
	
		if table.search(data.alsoFemales, nNdex) then
			io.write(makeRedirect(source, dest, 'f', ndex))
		end
	
		io.write(makeRedirect(source, dest, sex, ndex))
	end
end
