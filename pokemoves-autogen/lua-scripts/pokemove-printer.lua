--[[

Convert a data table for a Pokémon in PokéMoves to a string, also with indexing
and aliases, so that this output can be sourced by Lua.

This module returns a function with two arguments: the first is the Pokémon's
name, the second is the data table. The third parameter specifies whether breed
should be a reference to the base form's breed or not.

The COMPRESS local variable defines whether the output should be "compressed"
(ie: remove any useless space/newline etc...) or not. It can be used to create
a debug version of the module.

--]]
require('source-modules')

local COMPRESS = true

require('dumper')
-- luacheck: globals DataDumper

local pokes = require('Poké-data')
local evodata = require("Evo-data")
local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
local forms = require('Wikilib-forms')

local p = {}

-- From lua-scripts/lib.lua
-- Get the ndex from a key, that is either a number or a string. If it's a
-- string, it may be an ndex followed by an abbr or a name. If the key is an
-- ndex (possibly with an abbr) returns the numeric ndex, otherwise nil
local function getNdex(poke)
	if type(poke) == "number" then
		return poke
	end
	return type(poke) == "string" and tonumber(poke:match("%d+")) or nil
end

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
        ni = (s:find("\n", ni + 1) or i + 1) < i and (i - 10) or ni
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

local dumpTab = function(val, id)
    if COMPRESS then
        return DataDumper(val, id, true)
    else
        return (compressOutput(DataDumper(val, id, false, 2)))
    end
end

p.tabToStr = function(poke, data, breedref)
    local res = {}
    table.insert(res, "m[\"" .. poke .. "\"] = {")
    if not COMPRESS then
        table.insert(res, "\n")
    end
    -- ================================ LEVEL ================================
    table.insert(res, dumpTab(data.level, "level"))
    table.insert(res, ",")
    if not COMPRESS then
        table.insert(res, "\n")
    end
    -- ================================== TM ==================================
    -- Counterintuitively, compressTm is used when output is NOT compressed
    -- because is weaker than full compression and is usefull for legibility
    table.insert(res, COMPRESS and dumpTab(data.tm, "tm")
                      or compressTm(dumpTab(data.tm, "tm")))
    table.insert(res, ",")
    if not COMPRESS then
        table.insert(res, "\n")
    end
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
        table.insert(res, "\"].breed,")
        if not COMPRESS then
            table.insert(res, "\n")
        end
    else
        table.insert(res, COMPRESS and dumpTab(data.breed, "breed")
                          or compressBrd(dumpTab(data.breed, "breed")))
        table.insert(res, ",")
        if not COMPRESS then
            table.insert(res, "\n")
        end
    end
    -- ================================= TUTOR =================================
    table.insert(res, dumpTab(data.tutor, "tutor"))
    table.insert(res, ",")
    if not COMPRESS then
        table.insert(res, "\n")
    end
    -- ================================ PREEVO ================================
    table.insert(res, dumpTab(data.preevo, "preevo"))
    table.insert(res, ",")
    if not COMPRESS then
        table.insert(res, "\n")
    end
    -- ================================ EVENT ================================
    table.insert(res, dumpTab(data.event, "event"))
    table.insert(res, ",")
    if not COMPRESS then
        table.insert(res, "\n")
    end
    -- ================================ ALIASES ================================
    table.insert(res, "}\nm[")
    local abbr = forms.toEmptyAbbr(forms.getabbr(poke)) or ""
    if abbr ~= "" then
        table.insert(res, '"')
        table.insert(res, tostring(str.ff(pokes[poke].ndex)))
        table.insert(res, abbr)
        table.insert(res, '"')
    else
        table.insert(res, tostring(pokes[poke].ndex))
    end
    table.insert(res, "] = m[\"")
    table.insert(res, poke)
    table.insert(res, "\"]")
    if not COMPRESS then
        table.insert(res, "\n")
    end
    return table.concat(res)
end

p.allToDir = function(datas, dirname, skipkeys)
    skipkeys = skipkeys or {}
    -- Printing
    for poke, data in pairs(datas) do
        data.neighbours = nil
        -- "inf"ernape seems to be a number
        if not getNdex(poke) and not tab.search(skipkeys, poke) then
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
