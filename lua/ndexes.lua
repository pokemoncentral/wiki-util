--[[

Utility script to generate ndex lists.

This script generates list containing
ndex numbers, including alternative forms.
A list of all ndexes is ready-made.

--]]

local r = {}

local formUtil = require('Wikilib-forms')
local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local alts = require('AltForms-data')
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

return r
