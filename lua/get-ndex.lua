#!/usr/bin/lua
--[[

Utility script to get the ndex of a Pokémon given the name

Usage:
lua get-ndex.lua <poke> <kind>

--]]

if #arg < 1 then
    print("Missing mandatory arguments")
    print("Usage:")
    print("    lua get-ndex.lua <poke>")
    return 1
end

local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
-- local formlib = require('Wikilib-forms')
-- local evolib = require('Wikilib-evos')
-- local altdata = require("AltForms-data")
local pokes = require("Poké-data")

local gpoke = str.trim(arg[1]):lower() or "staraptor"

print(pokes[gpoke].ndex)
