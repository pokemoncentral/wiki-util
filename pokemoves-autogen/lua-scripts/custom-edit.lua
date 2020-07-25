--[[

This file constains custom edit that should be applied to learnlists
taken by the csvs. It can contain any hack you want, as well as any hack
GF put there in the first place.

It should return a function of signature (name, data) -> data
where name is the Pokémon name and data is the data table.

--]]

require('source-modules')

-- local evodata = require("Evo-data")
local tab = require('Wikilib-tables')  -- luacheck: no unused
local str = require('Wikilib-strings') -- luacheck: no unused
local pokes = require("Poké-data")
local multigen = require('Wikilib-multigen')
local learnlib = require('Wikilib-learnlists')

-- Steel Pokémon learn Raggio d'Acciaio, Dragon learn Dragobolide
local function typeTutors(poke, data)
    local pokedata = multigen.getGen(pokes[poke] or {}, 8)
    if tab.search(pokedata, "drago") then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].dragobolide = tab.map(tutorgames, function() return true end)
    end
    if tab.search(pokedata, "acciaio") then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8]["raggio d'acciaio"] = tab.map(tutorgames, function() return true end)
    end
    return data
end

-- Starters learns Radicalbero/Incendio/Idrocannone and Erbapatto/Fiammapatto/Acquapatto
local starterultimate = {
    erba = { "venusaur", "meganium", "sceptile", "torterra", "serperior",
    "chesnaught", "decidueye", "rillaboom" },
    fuoco = { "charizard", "typhlosion", "blaziken", "infernape",
    "emboar", "delphox", "incineroar", "cinderace" },
    acqua = { "blastoise", "feraligatr", "swampert", "empoleon",
    "samurott", "greninja", "primarina", "inteleon"},
}
local starterpatti = {
    erba = { "bulbasaur", "ivysaur", "venusaur", "chikorita", "bayleef",
    "meganium", "treecko", "grovyle", "sceptile", "turtwig", "grotle",
    "torterra", "snivy", "servine", "serperior", "pansage", "simisage",
    "chespin", "quilladin", "chesnaught", "rowlet", "dartrix", "decidueye",
    "silvally", "grookey", "thwackey", "rillaboom" },
    fuoco = { "charmander", "charmeleon", "charizard", "cyndaquil", "quilava",
    "typhlosion", "torchic", "combusken", "blaziken", "chimchar", "monferno",
    "infernape", "tepig", "pignite", "emboar", "pansear", "simisear", "fennekin",
    "braixen", "delphox", "litten", "torracat", "incineroar", "scorbunny",
    "raboot", "cinderace" },
    acqua = { "squirtle", "wartortle", "blastoise", "totodile", "droconaw",
    "feraligatr", "mudkip", "marshtomp", "swampert", "piplup", "prinplup",
    "empoleon", "oshawott", "dewott", "samurott", "panpour", "simipour",
    "froakie", "frogadier", "greninja", "popplio", "brionne", "primarina",
    "sobble", "drizzile", "inteleon"},
}
local function starters(poke, data)
    if tab.search(starterultimate.erba, poke) then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].radicalbero = tab.map(tutorgames, function() return true end)
    elseif tab.search(starterultimate.fuoco, poke) then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].incendio = tab.map(tutorgames, function() return true end)
    elseif tab.search(starterultimate.acqua, poke) then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].idrocannone = tab.map(tutorgames, function() return true end)
    end
    if tab.search(starterpatti.erba, poke) then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].erbapatto = tab.map(tutorgames, function() return true end)
    elseif tab.search(starterpatti.fuoco, poke) then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].fiammapatto = tab.map(tutorgames, function() return true end)
    elseif tab.search(starterpatti.acqua, poke) then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].acquapatto = tab.map(tutorgames, function() return true end)
    end
    return data
end

local function mewtm(poke, data)
    if poke == "mew" then
        data.tm = tab.map(data.tm, function() return { all = true } end)
    end
    return data
end

return function(poke, data)
    local hacks = { starters, typeTutors, mewtm }
    for _, f in ipairs(hacks) do
        data = f(poke, data)
    end
    return data
    -- return typeTutors(poke, starters(poke, data))
end
