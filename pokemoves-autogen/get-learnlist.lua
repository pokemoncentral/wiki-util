#!/usr/bin/lua
--[[

Usage:
lua get-learnlist.lua <poke> <kind>

--]]

-- Add the directory containing this script to package.path
-- NOTE: this works ONLY if the script is run from cmd, not if it's required
do
    -- Path is the path to the directory containing this script. If this is
    -- run from within the same directory it is empty, hence the check
    local path = arg[0]:match("(.-)[^/]+$")
    if path ~= "" then
        package.path = table.concat{ package.path, ";", path, "/?.lua" }
    end
end

require('source-modules')

local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
local formlib = require('Wikilib-forms')
local printer = require("static.print-learnlist8")
local altdata = require("AltForms-data")
local pokes = require("Poké-data")
local pmoves = require("PokéMoves-data")

local gpoke = str.trim(arg[1]):lower() or "staraptor"
local kind = str.trim(arg[2]):lower() or "level"

local function printOne(poke)
    return printer[kind](poke)
end

-- Check if the Poké has alternative forms
local pokealt = altdata[gpoke]
local res
local allequals = true
if pokealt then
    local basell = pmoves[gpoke][kind]
    -- For each form that has a learnlist, checks if it is the same as the base
    res = tab.map(pokealt.gamesOrder, function(abbr)
        local formname = gpoke .. formlib.toEmptyAbbr(abbr)
        local formextname = pokealt.names[abbr]
        formextname = formextname == "" and pokes[gpoke].name or formextname
        return { formextname, formname }
    end)
    res = tab.filter(res, function(pair)
        return pmoves[pair[2]] ~= nil
    end)
    -- print(table.concat(tab.map(res, table.concat)))
    allequals = tab.all(res, function(pair)
        return tab.equal(basell, pmoves[pair[2]][kind])
    end)
    -- print(allequals)
    res = tab.map(res, function(pair)
        return { pair[1], printOne(pair[2]) }
    end)

    -- for _, abbr in ipairs(pokealt.gamesOrder) do
    --     local formname = gpoke .. formlib.toEmptyAbbr(abbr)
    --     local formextname = pokealt.names[abbr]
    --     formextname = formextname == "" and pokes[gpoke].name or formextname
    --     if not tab.equal(basell, pmoves[formname][kind]) then
    --         allequals = false
    --     end
    --     table.insert(res, { formextname, printOne(formname) })
    -- end
end
if allequals then
    print(printOne(gpoke))
else
    tab.map(res, function(v)
        print("=====" .. v[1] .. "=====")
        print(v[2])
    end)
end
