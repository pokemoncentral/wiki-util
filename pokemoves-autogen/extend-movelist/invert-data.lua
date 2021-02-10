--[[

This script invert a single gen of pokemoves-data.

USAGE:
    lua invert-data.lua <gen>

Inverting only for a generation means that the output contains only
informations about learnsets for that generation. For instance, if gen
is 4 then the output stores, for each move, how Pokémon can learn it in
fourth gen (either via level, tm, breed or tutor).

The inverted module is stored in the "resultoutdir" directory
(specified in source-modules) as movepokes-data-<gen>.lua

========== Data structure ===========
The module exports a single table movepokes.
Keys in this table are a move names. Values are tables themselves.
The table for a move has always these keys: "level", "tm", "tutor", "breed"
To each of these keys is associated a table, whose keys are ndex and
values are tables with info about how that Pokémon can learn that move, in
the same format as (uncompressed) pokemoves-data.

--]]

-- luacheck: globals pokemoves tempoutdir resultoutdir
require('source-modules')(true)
-- luacheck: globals DataDumper
require('dumper')
local tab = require('Wikilib-tables') -- luacheck: no unused
local learnlist = require('learnlist-gen.learnlist')
local evodata = require("Evo-data")
local forms = require('Wikilib-forms')

local KINDS = {"level", "tm", "tutor", "breed"}

-- Path is the path to the directory containing this script. If this is
-- run from within the same directory it is empty, hence the check
local path = arg[0]:match("(.-)[^/]+$")
-- if path ~= "" then
--     path = path .. "/"
-- end

if #arg < 1 then
    print("Missing argument: generation required!")
    return 1
end
local gen = tonumber(arg[1]) or 4

-- ======================== COMPUTING INVERTED TABLE ========================
local movepokes = {}

-- Add an empty move table to movepokes if the specified move is not in
-- the table yet
local function addEmptyMove(movename)
    if not movepokes[movename] then
        movepokes[movename] = {}
        for _, kind in pairs(KINDS) do
            movepokes[movename][kind] = {}
        end
    end
end

local transformers = {
    level = function(val)
        val = learnlist.decompressLevelEntry(val, gen)
        return tab.map(val, function(va)
            return tab.map(va, function(v)
                if v == "inizio" then
                    return 1
                end
                return v
            end)
        end)
    end,
    breed = function(val, poke)
        local fbr = pokemoves[poke].breed == pokemoves[forms.uselessToEmpty(evodata[poke].name)].breed
                    and poke ~= evodata[poke].ndex
        if fbr then
            return nil
        else
            return val
        end
    end
}

for poke, data in pairs(pokemoves) do
    -- "inf"ernape seems to be a number
    if type(poke) == "number" or (tonumber(poke:sub(0, 3)) and poke ~= "infernape") then
        for _, kind in pairs(KINDS) do
            local pmkg = data[kind][gen]
            if kind == "tm" then
                for _, move in pairs(pmkg) do
                    addEmptyMove(move)
                    movepokes[move][kind][poke] = true
                end
            else
                for move, val in pairs(pmkg) do
                    addEmptyMove(move)
                    if transformers[kind] then
                        -- print(val, move, poke)
                        val = transformers[kind](val, poke)
                    end
                    movepokes[move][kind][poke] = val
                end
            end
        end
    end
end

-- ============================= WRITING OUTPUT =============================
-- This relies on some fact about executing directory of this script. It's
-- bad and I know it
print("Saved to \"" .. path .. "../" .. resultoutdir .. "/movepokes-data-" .. tostring(gen) .. ".lua\"")
local outfile = io.open(path .. "../" .. resultoutdir .. "/movepokes-data-" .. tostring(gen) .. ".lua", "w")
outfile:write(DataDumper(movepokes, "m", false, 2))
outfile:write("\n\nreturn m")
outfile:close()
