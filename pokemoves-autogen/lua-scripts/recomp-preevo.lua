#!/usr/bin/lua
--[[

This module recompute preevo learnsets for PokéMoves using other tables as
sources. After it prints to stdout the updated module.

--]]
-- luacheck: globals pokemoves tempoutdir
require('source-modules')

local pokes = require("Poké-data")
local evodata = require("Evo-data")
local tab = require('Wikilib-tables')
local evolib = require('Wikilib-evos')
local forms = require('Wikilib-forms')

local lib = require('lib')
local printer = require('pokemove-printer')

for poke, data in pairs(pokemoves) do
    for gen = 1,8 do
        if type(poke) == "string" and (not tonumber(poke:sub(0, 3)) or poke == "infernape")
           and evodata[poke] and poke ~= evodata[poke].name -- Isn't a base form
           then
            -- Compute preevo: iterate over all moves that preevo can learn
            local preevos = tab.map(evolib.preevoList(poke), forms.uselessToEmpty)
            local res = {}
            for _, preevo in pairs(preevos) do
                for _, move in pairs(lib.learnset(preevo, gen, {"preevo", "tutor"})) do
                    if not lib.canLearn(move, poke, gen, {"preevo", "event"}) then
                        if res[move] then
                            table.insert(res[move], pokes[preevo].ndex)
                        else
                            res[move] = { pokes[preevo].ndex }
                        end
                    elseif not lib.canLearn(move, poke, gen, {"preevo", "event", "tutor"}) then
                        -- The Pokémon can learn the move only by tutor, but the
                        -- preevo learn it another way, so it's all the games of
                        -- the generation
                        local tutorGames = lib.games.tutor[gen]
                        local mdata = data.tutor[gen][move]
                        local moveGames = tab.mapToNum(mdata, function(v, k)
                            return (not v) and tutorGames[k] or nil
                        end, ipairs)
                        if res[move] then
                            if res[move].games then
                                if not tab.equal(res[move].games, moveGames) then
                                    res[move].games = nil
                                else
                                    table.insert(res[move], pokes[preevo].ndex)
                                end
                            else
                                -- If the move is already there, just adds the
                                -- new Pokémon ignoring any sup
                                table.insert(res[move], pokes[preevo].ndex)
                            end
                        else
                            res[move] = {
                                pokes[preevo].ndex,
                                games = moveGames,
                            }
                        end
                    end
                end
                for move in pairs(pokemoves[preevo].tutor[gen]) do
                    -- Only moves learned by tutor from the preevo.
                    -- Assumption: if both the preevo and the Pokémon learn the
                    -- move by tutor, they learn it in the same games.
                    if not lib.canLearn(move, poke, gen, {"preevo", "breed", "event"}) then
                        if res[move] then
                            table.insert(res[move], pokes[preevo].ndex)
                        else
                            res[move] = { pokes[preevo].ndex }
                        end
                    end
                end
            end
            data.preevo[gen] = tab.map(res, function(t)
                t = tab.unique(t)
                table.sort(t)
                return t
            end)
        end
    end
end

-- Printing
printer.allToDir(pokemoves, tempoutdir .. "/luamoves-preevo")
