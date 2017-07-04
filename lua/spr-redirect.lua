--[[

This script creates redirects file for sprites
from one game to another, of Pokémon selected
with different criteria.

Arguments:
    - $1: specifies which redirect are
		to be created. Can be one
		of these:
		
		- 'all': Creates redirects for
			all Pokémon.
        - <Pokémon name/ndex>: Creates redirects
			for the specified Pokémon,
            alternative forms included.
		- <gen number>: Creates redirects
			for all Pokémon introduced in
			the first game of the given
			generation.
		- <game>: Creates redirects for
			all Pokémon and alternate
			forms introduced in the passed
			game.
	- $2: source game
	- $3: target game
	- $4: output file

--]]

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local isInGame = require('is-in-game')
local makeRedirect = require('dict-page').redirect
local pokes = require('Poké-data')
local data = require('Wikilib-data')
local ndexes = require('ndexes')

local allRedirects = function(source, dest, sex, ndex)
	local pages = {}

	for _, variant in pairs({'', 'd', 'sh', 'dsh'}) do
		local dest = string.interp(
			'File:Spr${game}${sex}${var}${ndex}.gif',
			{
				game = dest,
				sex = sex,
				var = variant,
				ndex = ndex
			}
		)
		local source = string.interp(
			'File:Spr${game}${sex}${var}${ndex}.gif',
			{
				game = source,
				sex = sex,
				var = variant,
				ndex = ndex
			}
		)

		table.insert(pages, makeRedirect(source, dest))
	end

	return table.concat(pages)
end

local sourceGame, destGame = arg[2], arg[3]

local source = tonumber(arg[1]) or arg[1]:lower()
if arg[1] == 'all' then
	source = ndexes.all

elseif pokes[source] then
    source = ndexes.forms(pokes[source].ndex, sourceGame)

elseif tonumber(arg[1]) then
	source = ndexes.gen(arg[1])

else
	source = ndexes.game(arg[1])
	
end

io.output(arg[4])

for _, ndex in pairs(source) do
    local nNdex = string.parseInt(ndex)
    
    local sex = 'm'
    if table.search(data.onlyFemales, nNdex) then
        sex = 'f'
    end

    if table.search(data.alsoFemales, nNdex) then
        io.write(allRedirects(sourceGame, destGame, 'f', ndex))
    end

    io.write(allRedirects(sourceGame, destGame, sex, ndex))
end
