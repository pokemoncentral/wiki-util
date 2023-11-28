#!/usr/bin/lua
--[[

Usage:
lua get-learnlist.lua <poke> <kind> <gen>

--]]

-- ============================= Input processing =============================
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
-- luacheck: globals pokemoves tempoutdir
require('source-modules')(true)

local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
local wlib = require('Wikilib')
local formlib = require('Wikilib-forms')
local evolib = require('Wikilib-evos')
local altdata = require("AltForms-data")
local pokes = require("Poké-data")

local gpoke = str.trim(arg[1]):lower() or "staraptor"
local kind = str.trim(arg[2]):lower() or "level"
local gen = tonumber(str.trim(arg[3]) or "8")
assert(gen >= 9, "the generation must be 9 or above")

local printer = require("learnlist-gen.print-learnlist" .. tostring(gen))

if #arg < 2 then
    print("Missing mandatory arguments")
    print("Usage:")
    print("    lua get-learnlist.lua <poke> <kind> <gen>")
    return 1
end

-- ================================== Utils ==================================
-- Print the learnlist of a single Pokémon/form in a single game
local function printOne(poke)
    return printer[kind](poke)
end

-- =================================== Main ===================================

-- If kind is tutor, nothing
if kind == "tutor" then
    print("")
    return 0
end
-- If kind is preevo, check if the Pokémon has preevo
if kind == "preevo" and not evolib.directPreevo(gpoke) then
    -- If not, returns the empty string because it shouldn't have a preevo
    -- table, not just a preevonull
    print("")
    return 0
end

-- Iterate on all alternative forms
local pokealt = altdata[gpoke]
if not pokealt then
    pokealt = { gamesOrder = { "base" }, names = { base = "" }}
end
-- We're only interested in forms with an learnlist
local interestingForms = tab.filter(pokealt.gamesOrder, function(abbr)
    local formname = gpoke .. formlib.toEmptyAbbr(abbr)
    return pokemoves[formname] ~= nil
end)
-- The learnlist data of the base form
local baselld = pokemoves[gpoke][kind]

-- First, check if all forms have the same learnlist data
local allequals = tab.all(interestingForms, function(abbr)
    local formname = gpoke .. formlib.toEmptyAbbr(abbr)
    return tab.equal(pokemoves[formname][kind], baselld)
end)
if allequals then
    print(printOne(gpoke))
    return 0
end

-- If there are differences, compute the learnlists per form and print them
local formlls = tab.map(interestingForms, function(abbr)
    -- For each form, compute the learnlist and the name of the section
    -- (extended name of the form)
    local formname = gpoke .. formlib.toEmptyAbbr(abbr)
    local formextname = pokealt.names[abbr]
    formextname = formextname == "" and pokes[gpoke].name or formextname
    return { formextname, printOne(formname) }
end)
for _, v in ipairs(formlls) do
    print("=====" .. v[1] .. "=====")
    print(v[2])
end
