#!/usr/bin/lua
--[[

This module recompute breed parents for PokéMoves using other tables as sources.
After it prints to stdout the updated module.

--]]
-- luacheck: globals pokemoves
require('source-modules')

local pokeeggs = require("PokéEggGroup-data")
local pokes = require("Poké-data")
local evodata = require("Evo-data")
local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
local learnlib = require('Wikilib-learnlists')
-- local evolib = require('Wikilib-evos')
local forms = require('Wikilib-forms')
local onlyFemale = require('Wikilib-data').onlyFemales

local printer = require('pokemove-printer')

local genderless = {
    "magnemite", "magneton", "voltorb", "electrode", "staryu", "starmie",
    "porygon", "porygon2", "shedinja", "lunatone", "solrock", "baltoy",
    "claydol", "beldum", "metang", "metagross", "bronzor", "bronzong",
    "magnezone", "porygon-z", "rotom", "phione", "manaphy", "klink", "klang",
    "klinklang", "cryogonal", "golett", "golurk", "carbink", "minior",
    "dhelmise"
}

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

local function compareNdex(a, b)
    -- TODO (?): use abbrLT if they are both strings (really needed?)
    if type(a) == type(b) then
        return a < b
    end
    local an = type(a) == "string" and tonumber(a:sub(0, 3)) or a
    local bn = type(b) == "string" and tonumber(b:sub(0, 3)) or b
    if an == bn then
        return type(a) == "number"
    else
        return an < bn
    end
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
-- an egg group that isn't "sconosciuto"). Pokémon of the same evoline, female
-- only and genderless Pokémon (because they can't pass an egg move) are
-- excluded from the list
local function eggNeighboursList(poke)
    local groups = tab.filter(pokeeggs[poke] or {},
                              function(g) return g ~= "sconosciuto" end)
    return tab.filter(tab.unique(tab.flatMap(groups, eggGroupList)), function(p)
        -- return not evolib.sameEvoLine(poke, p)
        --        and not tab.search(onlyFemale, p)
        return not tab.search(onlyFemale, p)
               and not tab.search(genderless, p)
    end)
end

-- Check whether a Pokémon has at least one parent to learn a move by breed
-- in a certain game
local function hasParent(move, poke, gen, gameidx)
    -- return pokemoves[poke].breed
    --        and pokemoves[poke].breed[gen]
    --        and pokemoves[poke].breed[gen][move]
    --        and pokemoves[poke].breed[gen][move][gameidx]
    return pokemoves[poke].breed[gen][move]
           and pokemoves[poke].breed[gen][move][gameidx][1]
end

-- Check if a Pokémon can learn a move by level in a certain game.
local function learnLevelGame(move, poke, gen, game)
    local idx = tab.search(learnlib.games.level[gen], game)
    return pokemoves[poke].level
           and pokemoves[poke].level[gen]
           and pokemoves[poke].level[gen][move]
           and pokemoves[poke].level[gen][move][idx][1]
end

-- Check if a Pokémon can learn a move by tutor in a certain game.
local function learnTutorGame(move, poke, gen, game)
    local idx = tab.search(learnlib.games.tutor[gen], game)
    return pokemoves[poke].tutor
           and pokemoves[poke].tutor[gen]
           and pokemoves[poke].tutor[gen][move]
           and pokemoves[poke].tutor[gen][move][idx]
end

-- The main algorithm is iterative, more or less Bellman-Ford. For each Pokémon
-- computes at each step the list of parents from which it can learn a move. A
-- Pokémon is not considered able to learn a move via breed unless it has at
-- least one parent listed for it. Iterating this procedure enough ensures that
-- parents are computed rights

-- First for each Pokémon computes the list of neighbours
for poke, data in pairs(pokemoves) do
    if not data.neighbours then
        pokemoves[poke].neighbours = eggNeighboursList(poke)
    end
end

-- Can modify gamedata, but has no other side effects. Return the new gamedata
local function recompPokeMoveGame(poke, gen, game, gameidx, move, gamedata)
    for _, opoke in pairs(pokemoves[poke].neighbours) do
        if pokemoves[opoke] then
            if learnlib.canLearn(move, opoke, gen, {"level", "breed", "preevo" ,"tutor"})
               or learnLevelGame(move, opoke, gen, game)
               or learnTutorGame(move, opoke, gen, game) then
                -- opoke can learn the move "easily" in this game
                if not gamedata.direct then
                    -- It was a chain before, but now it's direct, so empties
                    -- parents to remove chains
                    gamedata = { direct = true, games = gamedata.games }
                end
                local abbr = forms.getabbr(opoke)
                table.insert(gamedata, abbr == 'base'
                                       and pokes[opoke].ndex
                                       or (str.tf(pokes[opoke].ndex) .. abbr))
            elseif not gamedata.direct
                   and hasParent(move, opoke, gen, gameidx) then
                -- Isn't direct and opoke can learn by breed (in this game)
                gamedata.chain = true
                table.insert(gamedata, pokes[opoke].ndex)
            end
        end
    end
    return gamedata
end

-- Recomputes for one Pokémon, supposing other Pokémons are already correct.
-- Returns the new value for pokemoves[poke].breed[gen], without side effects.
local function recompOnePoke(poke, gen)
    -- Efficiency: copy only what is required, not a stupid table.copy
    local newbreeddata = {}
    for move, movedata in pairs(pokemoves[poke].breed[gen]) do
        newbreeddata[move] = { notes = movedata.notes, games = movedata.games }
        -- For all Pokémons in the same egg group checks whether it can learn
        -- the move directly or via breed.
        for gameidx, game in pairs(learnlib.games.breed[gen]) do
            -- If direct, parents are Pokémon that can learn the move
            -- directly, so are definitive: no need to recompute
            if not movedata[gameidx].direct and not movedata[gameidx].chain then
                newbreeddata[move][gameidx]
                    = recompPokeMoveGame(poke, gen, game, gameidx, move,
                                         tab.copy(movedata[gameidx]))
            else
                newbreeddata[move][gameidx] = movedata[gameidx]
            end
        end
    end
    return newbreeddata
end

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

-- Iterate recompOnePoke over all Pokémon about 14 (# egg groups) times.
for iteration = 1,14 do -- Actually iterations after the thrid are very quick,
    -- so it's not a big deal to do some some more
-- for iteration = 1,7 do -- it seems 7 is enough for any existing breed chain
    -- Do by rounds, not modifying inplace
    local newpokemoves = { }
    -- First iteration to add tables for any key, required to link them later
    -- for evolutions
    for poke, val in pairs(pokemoves) do
        newpokemoves[poke] = {
            level = val.level,
            tm = val.tm,
            breed = { nil, {}, {}, {}, {}, {}, {}, {} },
            tutor = val.tutor,
            preevo = val.preevo,
            event = val.event,
            neighbours = val.neighbours,
        }
    end
    for poke, _ in pairs(pokemoves) do
        -- Check if this Pokémon has a breed table or uses the one of the base
        -- form
        local basephasename = forms.uselessToEmpty(evodata[poke].name)
        if pokemoves[poke].breed == pokemoves[basephasename].breed
           and poke ~= evodata[poke].name then
            newpokemoves[poke].breed = newpokemoves[basephasename].breed
        else
            for gen = 2, 8 do
                if pokemoves[poke].breed[gen] then
                    newpokemoves[poke].breed[gen] = recompOnePoke(poke, gen)
                else
                    newpokemoves[poke].breed[gen] = nil
                end
            end
        end
    end
    pokemoves = newpokemoves
    print(iteration)
end


-- Remove pokemoves[poke].breed[gen][move].direct (? Or use it)
-- Keeping direct "should" allow to apply iterations on a non-empty set of
-- parents to udpate it. For now I'll try to remove it, but I'll decide
-- depending on the execution time

-- Unique parents, remove direct, compress games
for _, data in pairs(pokemoves) do
    for gen = 2,8 do
        if data.breed and data.breed[gen] then
            for move, movedata in pairs(data.breed[gen]) do
                if not movedata.new then
                    local newmovedata = { games = movedata.games,
                                          new = true }
                    for _, v in ipairs(movedata) do
                        v = tab.unique(v)
                        table.sort(v, compareNdex)
                        v.direct = nil
                        v.chain = nil
                        local mygame = v.games[1]
                        -- Remove games in which the Pokémon can't learn
                        -- the move
                        if not movedata.games
                           or tab.search(movedata.games, mygame) then
                            local found = false
                            for _, w in ipairs(newmovedata) do
                                if eqArray(v, w) then
                                    found = true
                                    table.insert(w.games, mygame)
                                end
                            end
                            if not found then
                                table.insert(newmovedata, v)
                            end
                        end
                    end
                    -- remove games field when is contains all games
                    if tab.equal(newmovedata[1].games,
                                 learnlib.games.breed[gen]) then
                        newmovedata[1].games = nil
                    end
                    data.breed[gen][move] = newmovedata
                end
            end
        end
    end
end

-- Add previous gens, remove field new added in the previous loop
for _, data in pairs(pokemoves) do
    for gen = 2,3 do
        -- if type(poke) == "string" and (not tonumber(poke:sub(0, 3))
        --                                or poke == "infernape")
        --    and data.breed and data.breed[gen] then
        if data.breed and data.breed[gen] then
            for _, mdata in pairs(data.breed[gen]) do
                mdata.new = nil
            end
        end
    end
    for gen = 4,8 do
        -- if type(poke) == "string" and (not tonumber(poke:sub(0, 3))
        --                                or poke == "infernape")
        --    and data.breed and data.breed[gen] then
        if data.breed and data.breed[gen] then
            for move, mdata in pairs(data.breed[gen]) do
                mdata.new = nil
                -- If the Pokémon doesn't have any parent, tries old gens
                for _, gdata in ipairs(mdata) do
                    if not gdata[1] then
                        for _, opoke in pairs(data.neighbours) do
                            if pokemoves[opoke]
                               and learnlib.learnPreviousGen(move, opoke, gen, 3) then
                                table.insert(gdata, pokes[opoke].ndex)
                            end
                        end
                    end
                end
            end
        end
    end
end

-- Printing
printer.allToDir(pokemoves, "luamoves-breed")
