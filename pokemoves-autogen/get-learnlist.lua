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
local function printOne(poke, game)
    return printer[kind](poke, game)
end

local strings = {
    TABS_HEADER = "{{Tabs/header|style=border}}",
    TABS_HEADERITEM = "{{Tabs/headeritem|n=${n}|title=${gameName}${active}}}",
    TABS_HEADERACTIVE = "|active=yes",
    TABS_BODY = "{{Tabs/body}}",
    TABS_ITEM = "{{Tabs/item|n=${n}${active}|content=\n${content}\n}}",
    TABS_FOOTER = "{{Tabs/footer}}",
}

-- Print the learnlist of a single Pokémon/form in all the games, including the
-- tabs code
local function printPoke(poke)
    -- Use the list of games in which the Pokémon exists provided by printer
    local games = tab.filter(printer.games[kind], function(game)
        return printer.existsInGame(poke, game)
    end)
    local gamells = tab.map(games, function(game)
        return printOne(poke, game)
    end)
    if tab.all(gamells, function(ll) return ll == gamells[1] end) then
        -- All equal, no tabs
        return gamells[1]
    else
        return table.concat({
            strings.TABS_HEADER,
            wlib.mapAndConcat(games, function(game, n)
                return str.interp(strings.TABS_HEADERITEM, {
                    n = n,
                    gameName = printer.getGameName[game],
                    active = printer.isGameActive(n) and strings.TABS_HEADERACTIVE or "",
                })
            end, "\n"),
            strings.TABS_BODY,
            wlib.mapAndConcat(gamells, function(ll, n)
                return str.interp(strings.TABS_ITEM, {
                    n = n,
                    content = ll,
                    active = printer.isGameActive(n) and strings.TABS_HEADERACTIVE or "",
                })
            end, "\n"),
            strings.TABS_FOOTER,
        }, "\n")
    end
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
    print(printPoke(gpoke))
    return 0
end

-- If there are differences, compute the learnlists per form and print them
local formlls = tab.map(interestingForms, function(abbr)
    -- For each form, compute the learnlist and the name of the section
    -- (extended name of the form)
    local formname = gpoke .. formlib.toEmptyAbbr(abbr)
    local formextname = pokealt.names[abbr]
    formextname = formextname == "" and pokes[gpoke].name or formextname
    return { formextname, printPoke(formname) }
end)
for _, v in ipairs(formlls) do
    print("=====" .. v[1] .. "=====")
    print(v[2])
end
