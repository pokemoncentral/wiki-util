#!/usr/bin/lua
--[[

Print Pokémon without breedref, to be used as standalone.

--]]
-- luacheck: globals pokemoves tempoutdir
require("source-modules")(true)

local printer = require("pokemove-printer")

printer.allToDir(pokemoves, tempoutdir .. "/luamoves-final", {}, true)
