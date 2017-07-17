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

local ndex = pokes[tonumber(arg[1])
        or arg[1]:lower()].ndex
local forms = require('AltForms-data')[ndex]
		or require('UselessForms-data')[ndex]
forms = table.map(forms.names, function(form)

	--[[
		Stripping unqualified form name,
		eg. 'Forma'
	--]] 
	return (form:match('^%S*%s*(.+)$'))
end)

io.output(io.open(arg[2], 'a'))

for abbr, form in pairs(forms) do
    if abbr ~= 'base' then
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
end

io.close()
