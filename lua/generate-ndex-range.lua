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
	
for ndex, data in pairs(useless) do
	if tonumber(ndex) then
		for abbr in pairs(data.names) do
			abbr = abbr == 'base' and '' or abbr
			table.insert(range, string.tf(ndex) .. abbr)
		end
	end
end

io.output(arg[1])

for _, poke in ipairs(range) do
	io.write(table.concat{arg[2], poke, arg[3], '\n'})
end
