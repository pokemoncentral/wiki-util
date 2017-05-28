--[[

This script writes a list of strings
containing all the ndex numbers,
alternative forms included, with given
prefix and suffix.

Arguments:
	- $1: output filename
	- $2: prefix
	- $3: suffix

--]]

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local ndexes = require('ndexes')

io.output(arg[1])

for _, poke in ipairs(ndexes.all) do
	io.write(table.concat{arg[2], poke, arg[3], '\n'})
end
