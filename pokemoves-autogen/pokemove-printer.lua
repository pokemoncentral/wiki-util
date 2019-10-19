--[[

Convert a data table for a Pokémon in PokéMoves to a string, also with indexing
and aliases, so that this output can be sourced by Lua.

This module returns a function with two arguments: the first is the Pokémon's
name, the second is the data table. The third parameter specifies whether breed
should be a reference to the base form's breed or not.

--]]
require('source-modules')

require('dumper')
-- luacheck: globals DataDumper

local pokes = require('Poké-data')
local evodata = require("Evo-data")
local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
local forms = require('Wikilib-forms')

local p = {}

local function compressOutput(s)
    return s:gsub("%{%s*%}", "{}")
            :gsub("%{%},%s*\n%s*%{%}", "{}, {}")
            :gsub("%{%},%s*\n%s*%{%}", "{}, {}")
            :gsub(" *\n", "\n")
end

local function compressPattern(pattern, spaces, s)
    s = s:gsub(pattern .. '\n%s*', '%1, ')
    local i = s:find(pattern)
    -- Numbers are empirically determined
    local ni = (s:find("{\n", 10) or 0) + 8
    while i ~= nil do
        ni = (s:find("\n", ni + 1)) < i and (i - 10) or ni
        if i - ni > 70 then
            s = table.concat{
                s:sub(0, i + 1),
                "\n", string.rep(" ", spaces),
                s:sub(i + 2)
            }
            ni = i
        end
        i = s:find(pattern, i + 1)
    end
    return s
end

local function compressTm(s)
    return compressPattern('("),', 7, s)
end
local function compressBrd(s)
    return compressPattern('(%d),', 11, s)
end

local dumpTab = function(...)
    return (compressOutput(DataDumper(...)))
end

p.tabToStr = function(poke, data, breedref)
    local res = {}
    table.insert(res, "m[\"" .. poke .. "\"] = {\n")
    -- ================================ LEVEL ================================
    table.insert(res, dumpTab(data.level, "level", false, 2))
    table.insert(res, ",\n")
    -- ================================== TM ==================================
    table.insert(res, compressTm(dumpTab(data.tm, "tm", false, 2)))
    table.insert(res, ",\n")
    -- ================================ BREED ================================
    if breedref then
        table.insert(res, "breed = m[\"")
        -- Some special cases
        -- if poke == "meowsticF" then
        --     table.insert(res, "espurr")
        -- elseif poke == "wormadamSa" or poke == "wormadamSc" then
        if poke == "wormadamSa" or poke == "wormadamSc" then
            table.insert(res, "burmy")
        else
            table.insert(res, evodata[poke].name)
        end
        table.insert(res, "\"].breed,\n")
    else
        table.insert(res, compressBrd(dumpTab(data.breed, "breed", false, 2)))
        table.insert(res, ",\n")
    end
    -- ================================= TUTOR =================================
    table.insert(res, dumpTab(data.tutor, "tutor", false, 2))
    table.insert(res, ",\n")
    -- ================================ PREEVO ================================
    table.insert(res, dumpTab(data.preevo, "preevo", false, 2))
    table.insert(res, ",\n")
    -- ================================ EVENT ================================
    table.insert(res, dumpTab(data.event, "event", false, 2))
    table.insert(res, ",\n")
    -- ================================ ALIASES ================================
    table.insert(res, "}\nm[")
    local abbr = forms.toEmptyAbbr(forms.getabbr(poke)) or ""
    if abbr ~= "" then
        table.insert(res, '"')
        table.insert(res, tostring(str.tf(pokes[poke].ndex)))
        table.insert(res, abbr)
        table.insert(res, '"')
    else
        table.insert(res, tostring(pokes[poke].ndex))
    end
    table.insert(res, "] = m[\"")
    table.insert(res, poke)
    table.insert(res, "\"]")
    return table.concat(res)
end

p.allToDir = function(datas, dirname, skipkeys)
    skipkeys = skipkeys or {}
    -- Printing
    for poke, data in pairs(datas) do
        data.neighbours = nil
        -- "inf"ernape seems to be a number
        if type(poke) == "string" and (not tonumber(poke:sub(0, 3)) or poke == "infernape")
           and not tab.search(skipkeys, poke) then
            -- compute breedref
            local fbr = datas[poke].breed == datas[forms.uselessToEmpty(evodata[poke].name)].breed
                        and poke ~= evodata[poke].name
            local outfile = io.open(dirname .. "/" .. poke .. ".lua", "w")
            outfile:write(p.tabToStr(poke, data, fbr))
            outfile:close()
        end
    end
end

return p
