local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local pokes = require('Poké-data')
local useless = require('UselessForms-data')

local range = table.keys(pokes)
range = table.filter(range, string.parseInt)
range = table.map(range, function(ndex)
	return type(ndex) == 'string'
			and ndex
			or string.tf(ndex)
end)

useless = table.filter(useless, function(_, key)
	return tonumber(key)
end)
	
for ndex, data in pairs(useless) do
	data = table.filter(data, function(_, abbr)
		return abbr ~= 'base'
	end)

	for abbr in pairs(data.names) do
		table.insert(range, string.tf(ndex) .. abbr)
	end
end

io.output(arg[1])

for _, poke in ipairs(range) do
	io.write(table.concat{arg[2], poke, arg[3], '\n'})
end
