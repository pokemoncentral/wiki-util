--[[

This script creates redirects file for artworks
of forms that lack a Sugimori version but have
a Dream World one.

Arguments
	- $1: ndex of the Pokémon
	- $2: output file

--]]

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local makeDict = require('dict-page')
local pokes = require('Poké-data')

local ndex = tonumber(arg[1])
local forms = require('AltForms-data')[ndex]
		or require('UselessForms-data')[ndex]
forms = table.map(forms.names, function(form)

	--[[
		Stripping unqualified form name,
		eg. 'Forma'
	--]] 
	return (form:match('^%S*%s*(.+)$'))
end)

io.output(arg[2])

for _, form in pairs(forms) do
	local title = string.interp(
		'File:Artwork${ndex}-${form}.png',
		{
			ndex = ndex,
			form = form
		}
	)
	local body = string.interp(
		'#RINVIA[[File:${ndex}${name} ${form} Dream.png]]',
		{
			ndex = ndex,
			name = pokes[ndex].name,
			form = form
		}
	)

	io.write(makeDict(title, body))
end