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
local formUtil = require('Wikilib-forms')
local makeRedirect = require('dict-page').redirect
local ms = require('MiniSprite')
local ndexes = require('ndexes')
local pokes = require('Poké-data')

--[[

Returns mini-sprite file name, already
prefixed by 'File:'

--]]
local getMsName = function(msType, ndex, gen)
    return ms[msType](ndex, gen):match('^%[%[(File:.-)%|')
end

local ndex = pokes[tonumber(arg[1])
        or arg[1]:lower()].ndex
local msType = string.lower(arg[3] or 'static')
        .. 'Lua'
local gen = arg[4] or ''

io.output(arg[2])

local source = getMsName(msType, ndex, gen)

-- arg[4] because nil is needed as default
local forms = ndexes.forms(ndex, arg[4])

for _, ndex in ipairs(forms) do
    if formUtil.getAbbr(ndex) ~= 'base' then
        local dest = getMsName(msType, ndex, gen)

        io.write(makeRedirect(source, dest))
    end
end
