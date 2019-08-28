#!/usr/bin/lua
--[[

This module recompute breed parents for PokéMoves using other tables as sources.
After it prints to stdout the updated module.

{
  blocco={ { 185, 299, 476 } },
  bodyguard={ { 557, games = { "XY" } }, { 476, games = { "ROZA" } } },
  centripugno={ { 074, 075, 076, 185 } },
  flagello={ { 185, 557, 558 }, games = { "ROZA" } },
  resistenza={ { 557 }, notes = "solo per volere del cusu" },
},

--]]
require('source-modules')

local pokemoves = require("PokéMoves-data")
local pokeeggs = require("PokéEggGroup-data")
local pokes = require("Poké-data")
local tab = require('Wikilib-tables')
local learnlib = require('Wikilib-learnlists')
local evolib = require('Wikilib-evos')
local onlyFemale = require('Wikilib-data').onlyFemales

local printer = require('pokemove-printer')

local skipkeys = { "games" }

-- Compare two tables, only on integer keys, to check if they're equal
local function eqArray(t1, t2)
    if #t1 ~= #t2 then
        return false
    end
    for k, v in ipairs(t1) do
        if v ~= t2[k] then
            return false
        end
    end
    return true
end

-- Returns the list of Pokémon with a certain egg group
local function eggGroupList(group)
    return tab.mapToNum(pokeeggs, function(v, k)
        if type(k) ~= "number"
           and (not tonumber(k:sub(0, 3)) or k == "infernape")
           and (v.group1 == group or v.group2 == group) then
            return k
        end
        return nil
    end)
end

-- Returns the list of Pokémon that can breed with a given one (that is: share
-- an egg group that isn't "sconosciuto"). Pokémon of the same evoline and
-- female only Pokémon (because they can't pass an egg move) are excluded
-- from the list
local function eggNeighboursList(poke)
    local groups = tab.filter(pokeeggs[poke] or {},
                              function(g) return g ~= "sconosciuto" end)
    return tab.filter(tab.unique(tab.flatMap(groups, eggGroupList)), function(p)
        return not evolib.sameEvoLine(poke, p) and not tab.search(onlyFemale, p)
    end)
end

-- Check whether a Pokémon has at least one parent to learn a move by breed
-- in a certain game
local function hasParent(move, poke, gen, gameidx)
    -- return pokemoves[poke].breed
    --        and pokemoves[poke].breed[gen]
    --        and pokemoves[poke].breed[gen][move]
    return pokemoves[poke].breed[gen][move]
           -- and pokemoves[poke].breed[gen][move][gameidx]
           and pokemoves[poke].breed[gen][move][gameidx][1]
end

-- Check if a Pokémon can learn a move by tutor in a certain game.
local function learnTutorGame(move, poke, gen, game)
    local _, idx = tab.deepSearch(pokemoves.games.tutor, game)
    if not pokemoves[poke].tutor or not pokemoves[poke].tutor[gen] then
        return false
    end
    return pokemoves[poke].tutor[gen][move]
           and pokemoves[poke].tutor[gen][move][idx]
end

-- The main algorithm is iterative, more or less Bellman-Ford. For each Pokémon
-- computes at each step the list of parents from which it can learn a move. A
-- Pokémon is not considered able to learn a move via breed unless it has at
-- least one parent listed for it. Iterating this procedure enough ensures that
-- parents are computed rights

-- First for each Pokémon computes the list of neighbours
for poke, data in pairs(pokemoves) do
    if not tab.search(skipkeys, poke) and not data.neighbours then
        pokemoves[poke].neighbours = eggNeighboursList(poke)
    end
end

local function recompPokeMoveGame(poke, gen, game, gameidx, move, movedata)
    for _, opoke in pairs(pokemoves[poke].neighbours) do
        if pokemoves[opoke] then
            if learnlib.canLearn(move, opoke, gen, {"breed", "preevo" ,"tutor"})
               or learnTutorGame(move, opoke, game) then
                -- opoke can learn the move "easily" in this game
                if not movedata[gameidx].direct then
                    -- It was a chain before, but now it's direct, so empties
                    -- parents to remove chains
                    movedata[gameidx] = { direct = true, games = movedata[gameidx].games }
                end
                table.insert(movedata[gameidx], pokes[opoke].ndex)
            elseif not movedata[gameidx].direct
                   and hasParent(move, opoke, gen, gameidx) then
                -- Isn't direct and opoke can learn by breed (in this game)
                table.insert(movedata[gameidx], pokes[opoke].ndex)
            end
        end
    end
end

-- Recomputes for one Pokémon, supposing other Pokémons are already correct.
local function recompOnePoke(poke, gen)
    if pokemoves[poke].breed and pokemoves[poke].breed[gen] then
        for move, movedata in pairs(pokemoves[poke].breed[gen]) do
            -- For all Pokémons in the same egg group checks whether it can learn the
            -- move directly or via breed.
            for gameidx, game in pairs(pokemoves.games.breed[gen]) do
                recompPokeMoveGame(poke, gen, game, gameidx, move, movedata)
            end
        end
    end
end

-- Iterate recompOnePoke over all Pokémon about 14 (# egg groups) times.
-- for iteration = 1,14 do
for iteration = 1,7 do -- it seems 7 is enough for any existing breed chain
    -- Do by rounds, not modifying inplace
    for poke, _ in pairs(pokemoves) do
        if type(poke) == "string" and (not tonumber(poke:sub(0, 3)) or poke == "infernape")
           and not tab.search(skipkeys, poke) then
            for gen = 2, 7 do
                recompOnePoke(poke, gen)
            end
        end
    end
    print(iteration)
end

-- Remove pokemoves[poke].breed[gen][move].direct (? Or use it)
-- Keeping direct "should" allow to apply iterations on a non-empty set of
-- parents to udpate it. For now I'll try to remove it, but I'll decide
-- depending on the execution time

-- Unique parents, remove direct, compress games
for poke, data in pairs(pokemoves) do
    if not tab.search(skipkeys, poke) then
        for gen = 2,7 do
            if data.breed and data.breed[gen] then
                for move, movedata in pairs(data.breed[gen]) do
                    -- Movedata is a reference to the computed value, so I can
                    -- safely create a new table for data.breed[gen][move]
                    data.breed[gen][move] = tab.filter(movedata, function(_, k)
                        return type(k) ~= "number"
                    end)
                    for _, v in ipairs(movedata) do
                        -- At this point each v has a single element in v.games
                        if not movedata.games or tab.search(movedata.games, v.games[1]) then
                            -- Clean up v: removes duplicated ndexes, sort and
                            -- remove direct
                            v = tab.unique(v)
                            table.sort(v)
                            v.direct = nil
                            -- Compress games: if the table is equal to one
                            -- already inserted, it simply merges their games
                            local eidx = nil
                            for k, g in ipairs(data.breed[gen][move]) do
                                if eqArray(v, g) then
                                    eidx = k
                                end
                            end
                            if eidx then
                                table.insert(movedata[eidx].games, v.games[1])
                            else
                                table.insert(data.breed[gen][move], v)
                            end
                        end
                    end
                end
            end
        end
    end
end

-- Add previous gens
for poke, data in pairs(pokemoves) do
    for gen = 4,7 do
        if type(poke) == "string" and (not tonumber(poke:sub(0, 3)) or poke == "infernape")
           and not tab.search(skipkeys, poke)
           and data.breed and data.breed[gen] then
            for move, mdata in pairs(data.breed[gen]) do
                -- If the Pokémon doesn't have any parent, tries old gens
                if not mdata[1][1] then
                    -- print("No breed parents", poke, gen, move)
                    for _, opoke in pairs(data.neighbours) do
                        -- if pokemoves[opoke] then print("Possible parent", opoke) end
                        if pokemoves[opoke] and learnlib.learnPreviousGen(move, opoke, gen, 3) then
                            table.insert(mdata[1], pokes[opoke].ndex)
                        end
                    end
                end
            end
        end
    end
end

-- Printing
printer.allToDir(pokemoves, "luamoves-breed", skipkeys)
