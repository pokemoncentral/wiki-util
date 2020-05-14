--[[

This script creates redirects file for
generic Pokémon sprites.

Arguments:
	- $1: specifies which redirect are
		to be created. Can be one
		of these:

		- 'all': Creates redirects for
			all Pokémon, using as target
			game the first of the latest
			generation.
		- <gen number>: Creates redirects
			for all Pokémon introduced in
			the first game of the given
			generation, using this as target
			game.
		- <game>: Creates redirects for
			all Pokémon and alternate
			forms introduced in the passed
			game, using it as target one.

	- $2: output filename

--]]

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local makeDict = require('dict-page')
local data = require('Wikilib-data')
local gendata = require('Gens-data')
local ndexes = require('ndexes')

local makeRedirect = function(source, sex, ndex)
	local body = string.interp(
		'#RINVIA[[File:${game}${sex}${ndex}.png]]',
		{
			game = source,
			sex = sex,
			ndex = ndex
		}
	)

	return makeDict(table.concat{'File:', ndex,
			'.png'}, body)
end

local source, actualGame
if arg[1] == 'all' then
	source = ndexes.all
	actualGame = gendata[gendata.latest].games[1]

elseif tonumber(arg[1]) then
	source = ndexes.gen(arg[1])
	actualGame = gendata[tonumber(arg[1])].games[1]

else
	source = ndexes.game(arg[1])
	actualGame = arg[1]

end
actualGame = string.fu(actualGame)

io.output(io.open(arg[2], 'a'))

for _, ndex in pairs(source) do
	local nNdex = string.parseInt(ndex)

	local sex = 'm'
	if table.search(data.onlyFemales, nNdex) then
		sex = 'f'
	end

	io.write(makeRedirect(actualGame, sex, ndex))
end

io.close()
