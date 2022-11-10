#!/usr/bin/lua
--[[

Compressions applied:

level: if all the tables are the same, store only one copy of the table.
	If this table then contains a single element, stores directly the element


Compressions proposed:

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


Compressions dropped:

tm can't be improved

breed: drop a nesting level when possible (ie: there's only one table)
DROPPED because it only saves 1MB (can be implemented if needed)

preevo: ? It's even worth to compress this? I think they're very small

--]]
-- luacheck: globals pokemoves tempoutdir
require('source-modules')(true)

local tab = require('Wikilib-tables')

local printer = require('pokemove-printer')

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

-- Uses pokemoves because it's easier to print afterward
-- Clean up pokemoves from keys that aren't Pokémon names, this simplify a
-- little the iteration afterwards
local tmppokemoves = {}
for poke, val in pairs(pokemoves) do
    if not getNdex(poke) then
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
			if #v2 == 1 and #v2[1] == 1 then
				v1[move] = v2[1][1]
			end
		end
	end

    -- -- breed = drop a nesting level when possible (ie: there's only one table)
	-- for _, v1 in pairs(data.breed) do -- key is gen
	-- 	-- v1 = { move = { ... }, ...}
	-- 	for move, v2 in pairs(v1) do -- key is move
	-- 		-- v2 = { { <array of levels for first game> }, { <array for second game> }, ... }
	-- 		if #v2 == 1 and type(v2[1]) == "table" then
	-- 			v1[move] = v2[1]
    --          -- beware of breed notes
	-- 		end
	-- 	end
	-- end

    -- tutor: storing the table by "colums" instead of "rows"
    -- not applied because right now I don't need it
    -- for g, v1 in pairs(data.tutor) do -- key is gen
    --     -- v1 = { move = { ... }, ...}
    --     local _, elem = next(v1)
    --     if elem then
    --         local res = {}
    --         for _ = 1, #elem  + 1 do
    --             table.insert(res, {})
    --         end
    --         for move, v2 in pairs(v1) do -- key is move
    --             -- v2 = { <array of bool for all the games> }
    --             table.insert(res[1], move)
    --             for i, v in ipairs(v2) do
    --                 table.insert(res[i + 1], v)
    --             end
    --         end
    --         data.tutor[g] = res
    --     end
    -- end
end

-- Printing
printer.allToDir(pokemoves, tempoutdir .. "/luamoves-compress")
