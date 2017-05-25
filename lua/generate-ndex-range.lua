local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local pokes = require('Poké-data')
local useless = require('UselessForms-data')

local range = table.keys(pokes)
for ndex, data in ipairs(useless) do
	for abbr in pairs(data.names) do
		table.insert(range, string.tf(ndex) .. abbr)
	end
end

io.output(arg[1])

for poke in ipairs(range) do
	io.write(table.concat{arg[2], poke, arg[3], '\n'})
end
