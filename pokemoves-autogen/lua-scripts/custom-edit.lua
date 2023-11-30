--[[

This file constains custom edit that should be applied to learnlists
taken by the csvs. It can contain any hack you want, as well as any hack
GF put there in the first place.

It should return a function of signature (name, data) -> data
where name is the Pokémon name and data is the data table.

--]]

require("source-modules")

local tab = require("Wikilib-tables")
local pokes = require("Poké-data")
local multigen = require("Wikilib-multigen")
local learnlib = require("Wikilib-learnlists")

-- Dragon Pokémon learn Dragobolide, Steel learn Raggio d'Acciaio but not in DLPS
local function typeTutors(poke, data)
    local pokedata = multigen.getGen(pokes[poke] or {}, 8)
    if tab.search(pokedata, "drago") then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8].dragobolide = tab.map(tutorgames, function()
            return true
        end)
    end
    if tab.search(pokedata, "acciaio") then
        local tutorgames = learnlib.games.tutor[8]
        data.tutor[8]["raggio d'acciaio"] = tab.map(tutorgames, function(game)
            return game ~= "DLPS"
        end)
    end
    return data
end

-- Starters learns Radicalbero/Incendio/Idrocannone,
-- and in SpSc also Erbapatto/Fiammapatto/Acquapatto
local starterultimate = {
    -- stylua: ignore
    erba = {
        "venusaur", "meganium", "sceptile", "torterra", "serperior",
        "chesnaught", "decidueye", "rillaboom",
    },
    -- stylua: ignore
    fuoco = {
        "charizard", "typhlosion", "blaziken", "infernape", "emboar", "delphox",
        "incineroar", "cinderace",
    },
    -- stylua: ignore
    acqua = {
        "blastoise", "feraligatr", "swampert", "empoleon", "samurott",
        "greninja", "primarina", "inteleon",
    },
}
local starterpatti = {
    -- stylua: ignore
    erba = {
        "bulbasaur", "ivysaur", "venusaur", "chikorita", "bayleef", "meganium",
        "treecko", "grovyle", "sceptile", "turtwig", "grotle", "torterra",
        "snivy", "servine", "serperior", "pansage", "simisage", "chespin",
        "quilladin", "chesnaught", "rowlet", "dartrix", "decidueye",
        "silvally", "grookey", "thwackey", "rillaboom",
    },
    -- stylua: ignore
    fuoco = {
        "charmander", "charmeleon", "charizard", "cyndaquil", "quilava",
        "typhlosion", "torchic", "combusken", "blaziken", "chimchar",
        "monferno", "infernape", "tepig", "pignite", "emboar", "pansear",
        "simisear", "fennekin", "braixen", "delphox", "litten", "torracat",
        "incineroar", "scorbunny", "raboot", "cinderace",
    },
    -- stylua: ignore
    acqua = {
        "squirtle", "wartortle", "blastoise", "totodile", "droconaw",
        "feraligatr", "mudkip", "marshtomp", "swampert", "piplup", "prinplup",
        "empoleon", "oshawott", "dewott", "samurott", "panpour", "simipour",
        "froakie", "frogadier", "greninja", "popplio", "brionne", "primarina",
        "sobble", "drizzile", "inteleon",
    },
}

local function starters(poke, data)
    local tutorgames = learnlib.games.tutor[8]
    if tab.search(starterultimate.erba, poke) then
        data.tutor[8].radicalbero = tab.map(tutorgames, function()
            return true
        end)
    elseif tab.search(starterultimate.fuoco, poke) then
        data.tutor[8].incendio = tab.map(tutorgames, function()
            return true
        end)
    elseif tab.search(starterultimate.acqua, poke) then
        data.tutor[8].idrocannone = tab.map(tutorgames, function()
            return true
        end)
    end
    if tab.search(starterpatti.erba, poke) then
        data.tutor[8].erbapatto = tab.map(tutorgames, function(game)
            return game ~= "DLPS"
        end)
    elseif tab.search(starterpatti.fuoco, poke) then
        data.tutor[8].fiammapatto = tab.map(tutorgames, function(game)
            return game ~= "DLPS"
        end)
    elseif tab.search(starterpatti.acqua, poke) then
        data.tutor[8].acquapatto = tab.map(tutorgames, function(game)
            return game ~= "DLPS"
        end)
    end
    return data
end

local function mewtm(poke, data)
    if poke == "mew" then
        data.tm = tab.map(data.tm, function(d)
            d.all = true
            return d
        end)
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
