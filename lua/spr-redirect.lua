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
    - $2: flag, wether or not redirects should
        be created for back sprites. Defaults to
        false
	- $3: source game
	- $4: target game
	- $5: output file

--]]

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local isInGame = require('is-in-game')
local makeRedirect = require('dict-page').redirect
local spr = require('Spr').sprLua
local pokes = require('Poké-data')
local data = require('Wikilib-data')
local ndexes = require('ndexes')

local sprite = function(ndex, dest, var)
    return spr(ndex, dest, var)
            :match('%[%[([^|]+)|?.*%]%]')
end

local allRedirects = function(source, dest, variants, sex, ndex)
	local pages = {}

	for _, variant in pairs(variants) do
        local var = string.trim(table.concat{sex, ' ', variant})

		local dest = sprite(ndex, dest, var)
		local source = sprite(ndex, source, var)

		table.insert(pages, makeRedirect(source, dest))
	end

	return table.concat(pages)
end

-- Sourcegame is necessary for source
local sourceGame, destGame = arg[3], arg[4]

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

local variants = (arg[2] ~= 'false' and arg[2])
        and {'', 'back', 'shiny', 'back shiny'}
        or {'', 'shiny'}

io.output(io.open(arg[5], 'a'))

for _, ndex in pairs(source) do
    local nNdex = string.parseInt(ndex)
    
    local sex = 'male'
    if table.search(data.onlyFemales, nNdex) then
        sex = 'female'
    end

    if table.search(data.alsoFemales, nNdex) then
        io.write(allRedirects(sourceGame, destGame,
                variants, 'female', ndex))
    end

    io.write(allRedirects(sourceGame, destGame, variants,
            sex, ndex))
end

io.close()
