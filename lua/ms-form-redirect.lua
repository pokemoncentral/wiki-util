--[[

This script creates mini sprites
redirect for the forms of a single
Pokémon to the basic one, for the
provided generation.

Arguments:
    - $1: Ndex/Name of the Pokémon
    - $2: Output file
    - $3: Optional, static/animated
        mini-sprite. Defaults to static.
        One of:
        - static
        - ani
    - $4: Optional, mini-sprites
        generation

--]]

local txt = require('Wikilib-strings')
local makeDict = require('dict-page')
local ms = require('MiniSprite')
local pokes = require('Poké-data')

--[[

Returns mini-sprite file name, already
prefixed by 'File:'

--]]
local getMsName = function(msType, ndex, abbr, gen)
    return ms[msType](ndex .. (abbr or ''), gen)
            :match('^%[%[(File:.-)%|')
end

local ndex = pokes[tonumber(arg[1])
        or arg[1]:lower()].ndex
local msType = string.lower(arg[3] or 'static')
        .. 'Lua'
local gen = arg[4] or ''

io.output(arg[2])

local body = table.concat{
    '#RINVIA[[',
    getMsName(msType, ndex, nil, gen),
    ']]'
}

local forms = require('AltForms-data')[ndex]
		or require('UselessForms-data')[ndex]

for _, abbr in ipairs(forms.gamesOrder) do
    if abbr ~= 'base' then
        local title = getMsName(msType, ndex, abbr, gen)

        io.write(makeDict(title, body))
    end
end
