#!/usr/bin/lua

-- luacheck: globals tempoutdir
require("source-modules")

local evodata = require("Evo-data")
local tab = require("Wikilib-tables")
local str = require("Wikilib-strings")

local lib = require("lib")
local tweaks = require("custom-edit")
local printer = require("pokemove-printer")

local function ParseCSVLine(line, sep)
    local res = {}
    local pos = 1
    sep = sep or ","
    while true do
        local c = string.sub(line, pos, pos)
        if c == "" then
            break
        end
        if c == '"' then
            -- quoted value (ignore separator within)
            local txt = ""
            repeat
                local startp, endp = string.find(line, '^%b""', pos)
                txt = txt .. string.sub(line, startp + 1, endp - 1)
                pos = endp + 1
                c = string.sub(line, pos, pos)
                if c == '"' then
                    txt = txt .. '"'
                end
            -- check first char AFTER quoted string, if it is another
            -- quoted string without separator, then append it
            -- this is the way to "escape" the quote char in a quote. example:
            --   value1,"blub""blip""boing",value3  will result in blub"blip"boing  for the middle
            until c ~= '"'
            table.insert(res, txt)
            assert(c == sep or c == "")
            pos = pos + 1
        else
            -- no quotes used, just look for the first separator
            local startp, endp = string.find(line, sep, pos)
            if startp then
                table.insert(res, string.sub(line, pos, startp - 1))
                pos = endp + 1
            else
                -- no separator found -> use rest of string and terminate
                table.insert(res, string.sub(line, pos))
                break
            end
        end
    end
    return res
end

local datagen = { {}, {}, {}, {}, {}, {}, {}, {}, {} }
local data = {
    level = tab.copy(datagen),
    tm = tab.copy(datagen),
    breed = tab.copy(datagen),
    tutor = tab.copy(datagen),
    preevo = {},
    event = {},
}

-- List of Pokémon which are base form but don't learn any move via breed
-- stylua: ignore
local baseNoBreed = {
    "caterpie", "weedle", "magnemite", "voltorb", "tauros", "magikarp",
    "ditto", "porygon", "articuno", "zapdos", "moltres", "mewtwo", "mew",
    "unown", "smeargle", "raikou", "entei", "suicune", "lugia", "ho-oh",
    "celebi", "wurmple", "lunatone", "solrock", "baltoy", "wynaut", "beldum",
    "regirock", "regice", "registeel", "latias", "latios", "kyogre", "groudon",
    "rayquaza", "jirachi", "deoxys", "kricketot", "burmy", "combee", "bronzor",
    "rotom", "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran",
    "regigigas", "giratina", "cresselia", "phione", "darkrai", "shaymin",
    "arceus", "victini", "throh", "sawk", "klink", "tynamo", "cryogonal",
    "golett", "rufflet", "cobalion", "terrakion", "virizion", "tornadus",
    "thundurus", "reshiram", "zekrom", "landorus", "kyurem", "keldeo",
    "meloetta", "genesect", "carbink", "xerneas", "yveltal", "zygarde",
    "diancie", "hoopa", "volcanion", "tipo zero", "minior", "dhelmise",
    "tapu koko", "tapu lele", "tapu bulu", "tapu fini", "cosmog", "nihilego",
    "buzzwole", "pheromosa", "xurkitree", "celesteela", "kartana", "guzzlord",
    "necrozma", "magearna", "marshadow", "poipole", "stakataka", "blacephalon",
    "zeraora", "meltan", "sinistea", "impidimp", "falinks", "dracozolt",
    "arctozolt", "dracovish", "arctovish", "zacian", "zamazenta", "eternatus",
    "kubfu", "zarude", "regieleki", "regidrago", "glastrier", "spectrier",
    "calyrex", "enamorus", "gimmighoul", "grandizanne", "fungofurioso",
    "peldisabbia", "codaurlante", "crinealato", "alirasenti", "lunaruggente",
    "solcoferreo", "falenaferrea", "manoferrea", "colloferreo", "spineferree",
    "saccoferreo", "eroeferreo", "ting-lu", "chien-pao", "wo-chien", "chi-yu",
    "koraidon", "miraidon", "acquecrespe", "fogliaferrea", "poltchageist",
    "okidogi", "munkidori", "fezandipiti", "ogerpon", "vampeaguzze",
    "furiatonante", "capoferreo", "massoferreo", "terapagos", "pecharunt",
    -- Forms
    "deoxysA", "deoxysD", "deoxysV", "shayminC", "kyuremN", "kyuremB",
    "hoopaL", "articunoG", "zapdosG", "moltresG", "calyrexG", "calyrexS",
    "palafinP", "gimmighoulA", "ursalunaL", "ogerponP", "ogerponFn",
    "ogerponFc",
}
-- List of non-base Pokémon with a breed list different from that of their base
-- form (mostly Pokémon with a baby form). Only used up to gen 8
-- stylua: ignore
local breedNoBase = {
    "chansey", "chimecho", "mantine", "marill", "mr. mime", "roselia",
    "snorlax", "sudowoodo", "mr. mimeG"
}

local poke = str.trim(arg[1]) or "staraptor"

local outfile = io.open(tempoutdir .. "/luamoves/" .. poke .. ".lua", "w")

for line in io.lines(tempoutdir .. "/pokecsv/" .. poke .. ".csv") do
    line = tab.map(ParseCSVLine(line), str.trim)
    local kind = line[2]
    local gen = tonumber(line[3])
    local move = line[1]
    if kind == "tm" then
        if not data.tm[gen][move] then
            data.tm[gen][move] = { line[4] }
        elseif not tab.search(data.tm[gen][move], line[4]) then
            table.insert(data.tm[gen][move], line[4])
        end
    elseif kind == "tutor" then
        local tutorgames = lib.games.tutor[gen]
        data.tutor[gen][move] = data[kind][gen][move]
            or tab.map(tutorgames, function()
                return false
            end)
        data.tutor[gen][move][tab.search(tutorgames, line[4])] = true
    elseif kind == "breed" then
        local breedsgames = lib.games.breed[gen]
        if not data.breed[gen][move] then
            data.breed[gen][move] = tab.map(breedsgames, function(v)
                return { games = { v } }
            end)
            data.breed[gen][move].games = {}
        end
        table.insert(data.breed[gen][move].games, line[4])
    elseif kind == "level" then
        if line[4] ~= "Colo" and line[4] ~= "XD" then
            local levelgames = lib.games.level[gen]
            data.level[gen][move] = data.level[gen][move]
                or tab.map(levelgames, function()
                    return {}
                end)
            table.insert(
                data.level[gen][move][tab.search(levelgames, line[4])],
                line[5]
            )
        end
    elseif kind == "reminder" then
        -- Add reminder moves to level moves with level -1
        local levelgames = lib.games.level[gen]
        data.level[gen][move] = data.level[gen][move]
            or tab.map(levelgames, function()
                return {}
            end)
        table.insert(
            data.level[gen][move][tab.search(levelgames, line[4])],
            "-1"
        )
    elseif
        not (poke == "pichu" and kind == "light-ball-egg")
        and not (poke == "pikachu" and kind == "pika-surf")
        and not (poke == "rotom" and kind == "form-change")
    then
        -- It's easy to find these because lua interpreter report an error
        outfile:write(
            "\n\n==========================================================\n"
        )
        outfile:write(
            "========================= ERRORE =========================\n"
        )
        outfile:write(poke, kind, gen, move)
    end
end

-- After building the raw data, some refinement

-- breed with all games can have the field "games" removed
data.breed = tab.map(data.breed, function(g, gen)
    return tab.map(g, function(d, _)
        if #d.games == #lib.games.breed[gen] then
            d.games = nil
        end
        return d
    end)
end)
-- level polishing: mapping 1 -> "inizio" and 0 -> "evo"
for _, v1 in pairs(data.level) do
    -- v1 = { move = { ... }, ...}
    for _, v2 in pairs(v1) do
        -- v2 = { { <array of levels for first game> }, { <array for second game> }, ... }
        for k, v3 in pairs(v2) do
            -- v3 = { <array of levels for first game> }
            v2[k] = tab.map(v3, function(l)
                if l == "0" then
                    return "evo"
                elseif l == "1" then
                    return "inizio"
                elseif l == "-1" then
                    return "ricorda"
                else
                    return tonumber(l)
                end
            end)
        end
    end
end
-- TODO: no support for events

-- Compute breedref and log
local nobreed = true
for _, v in pairs(data.breed) do
    if next(v) ~= nil then
        nobreed = false
    end
end
-- if no breed takes the ones of the base form. Moreover if a non-base form
-- has a breed, logs it
if nobreed then
    if tab.search(baseNoBreed, poke) then
        nobreed = false
    elseif poke == evodata[poke].name then
        print("No breed for base phase: " .. poke)
    end
else
    if poke ~= evodata[poke].name and not tab.search(breedNoBase, poke) then
        print("Breed for no-base phase: " .. poke)
    end
end

-- Applies tweaks
data = tweaks(poke, data)

outfile:write(printer.tabToStr(poke, data, nobreed))
outfile:close()
