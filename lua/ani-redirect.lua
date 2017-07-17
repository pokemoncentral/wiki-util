--[[

This script creates redirects file for
mini-sprite of the current generation
from animated to static.

Arguments:
	- $1: specifies which redirect are
		to eb created. Can be one
		of these:
		- 'all': Creates redirects for
			all Pokémon.
		- <gen number>: Creates redirects
			for all Pokémon introduced in
			in the first game of the given
			generation.
		- <game>: Creates redirects for
			all Pokémon and alternate
			forms introduced in the passed
			game.
	- $2: output filename

--]]

local str = require('Wikilib-strings')
local makeDictPage = require('dict-page')
local ndexes = require('ndexes')

local source
if arg[1] == 'all' then
	source = ndexes.all
	
elseif tonumber(arg[1]) then
	source = ndexes.gen(arg[1])
	
else
	source = ndexes.game(arg[1])
	
end

io.output(io.open(arg[2], 'a'))

for _, ndex in pairs(source) do
	local title = string.interp(
		'File:Ani${ndex}MS.gif',
		{
			ndex = ndex
		}
	)
	local content = string.interp(
		'#RINVIA [[File:${ndex}MS.png]]',
		{
			ndex = ndex
		}
	)

	io.write(makeDictPage(title, content))
end

io.close()
