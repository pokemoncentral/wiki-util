#!/usr/bin/lua
--[[

Compressions applied:

level: if all the tables are the same, store only one copy of the table.
	If this table then contains a single element, stores directly the element

Compressions proposed:

tm can't be improved

tutor: actually is
    movename -> array of fixed length
this can be easily improved storing this table by "colums" instead of "rows",
ie:
move1 -> {true  true}
move2 -> {true  true}
move3 -> {false true}
move4 -> {false false}
move5 -> {false false}
stored as
{move1, move2, move3, move4, move5}
{true, true, false, false, false}
{true, true, true, false, false}

breed: drop a nesting level when possible (ie: there's only one table and that
table doesn't have games)

preevo: ? It's even worth to compress this? I think they're very small

--]]
-- luacheck: globals pokemoves
require('source-modules')

-- local evodata = require("Evo-data")
local tab = require('Wikilib-tables')
-- local str = require('Wikilib-strings')
-- local learnlib = require('Wikilib-learnlists')

local printer = require('pokemove-printer')

-- Uses pokemoves because it's easier to print afterward
-- Clean up pokemoves from keys that aren't Pokémon names, this simplify a
-- little the iteration afterwards
local tmppokemoves = {}
for poke, val in pairs(pokemoves) do
    if type(poke) == "string" and (not tonumber(poke:sub(0, 3)) or poke == "infernape") then
        -- val.breed = { nil, {}, {}, {}, {}, {}, {} }
        tmppokemoves[poke] = val
    end
end
pokemoves = tmppokemoves

for _, data in pairs(pokemoves) do
	-- level: if all the tables are the same, store only one copy of the table.
	-- 	If this table then contains a single element, stores directly the element
	for _, v1 in pairs(data.level) do -- key is gen
		-- v1 = { move = { ... }, ...}
		for move, v2 in pairs(v1) do -- key is move
			-- v2 = { { <array of levels for first game> }, { <array for second game> }, ... }
			if tab.all(v2, function(t) return tab.equal(t, v2[1]) end) then
				v1[move] = { v2[1] }
			end
			if #v2[1] == 1 then
				v1[move] = v2[1][1]
			end
		end
	end
end

-- Printing
printer.allToDir(pokemoves, "luamoves-compress")
