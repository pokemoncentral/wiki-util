--[[

Script to build learnlist-entry calls from pokemoves-data

TODO: support alltm

--]]
-- luacheck: globals pokemoves tempoutdir
require('source-modules')

local p = {}

local str = require("Wikilib-strings")
local tab = require("Wikilib-tables")
local learnlib = require('Wikilib-learnlists')
local wlib = require('Wikilib')
local genlib = require('Wikilib-gens')
local multigen = require('Wikilib-multigen')
local formlib = require('Wikilib-forms')
local learnlist = require('learnlist-gen.learnlist')
local moves = require("Move-data")
local pokes = require("Poké-data")
local altdata = require("AltForms-data")
local pokemoves = require("learnlist-gen.pokemoves-data")
local libgames = require("lua-scripts.lib").games

local gen = 9

p.strings = {
    HF = "{{#invoke: Learnlist/hf | ${kind}${hf} | ${poke} | ${type1} | ${type2} | ${genh} | ${genp} }}",
    NULLENTRY = "{{#invoke: Learnlist/entry9 | ${kind}null}}",
    ENTRYHEAD = "{{#invoke: render | render | Modulo:Learnlist/entry9 | ${kind} | //",
    ENTRYFOOT = "}}",
    ENTRIES = {
        level = "|${move}|${STAB}|${notes}|${level}| //",
        tm = "|${move}|${STAB}|${notes}|${tmnum}| //",
        breed = "|${move}|${STAB}|${notes}| //",
        tutor = "|${move}|${STAB}|${notes}|${yn}| //",
        preevo = "|${move}|${STAB}|${poke1}${poke2} //",
    }
}
p.strings.HEADER = str.interp(p.strings.HF, { hf = "h" })
p.strings.FOOTER = str.interp(p.strings.HF, { hf = "f" })

-- Exports for get-learnlist
p.games = learnlist.filterGames(libgames, gen)
p.getGameName = {
    SV = "Ver 1.2.0",
    ["SV-2"] = "Ver 2.0.1",
}
-- 2 is the index of "SV-2"
p.isGameActive = function(num) return num == 2 end

p.computeSTAB = learnlist.computeSTAB

-- Checks whether the entry is alltm
p.alltm = function(kind, pmkindgen)
    return kind == "tm" and pmkindgen.all
end

-- These Pokémon weren't in SV, and were added in SV-2
local pokesSV2 = {
    "aipom", "ambipom", "arbok", "ariados", "bellsprout", "chandelure",
    "charjabug", "chimchar", "chimecho", "chingling", "clefable", "clefairy",
    "cleffa", "conkeldurr", "corphish", "cramorant", "crawdaunt", "cutiefly",
    "darkrai", "dipplin", "ducklett", "dusclops", "dusknoir", "duskull",
    "ekans", "empoleon", "feebas", "fezandipiti", "furret", "geodude",
    "gligar", "gliscor", "golem", "graveler", "grotle", "grubbin", "gurdurr",
    "hakamo-o", "hoothoot", "illumise", "infernape", "jangmo-o", "jirachi",
    "koffing", "kommo-o", "lampent", "leavanny", "litwick", "lombre", "lotad",
    "ludicolo", "magcargo", "mamoswine", "manaphy", "mandibuzz", "mienfoo",
    "mienshao", "mightyena", "milotic", "monferno", "morpeko", "munchlax",
    "munkidori", "ninetales", "noctowl", "nosepass", "nuzleaf", "ogerpon",
    "okidogi", "phantump", "phione", "piloswine", "piplup", "politoed",
    "poliwag", "poliwhirl", "poliwrath", "poltchageist", "poochyena",
    "prinplup", "probopass", "ribombee", "sandshrew", "sandslash", "seedot",
    "sentret", "sewaddle", "shaymin", "shiftry", "sinistcha", "slugma",
    "snorlax", "spinarak", "swadloon", "swanna", "swinub", "timburr",
    "torterra", "trevenant", "turtwig", "victreebel", "vikavolt", "volbeat",
    "vullaby", "vulpix", "weepinbell", "weezing", "yanma", "yanmega",
    -- New Pokémon, not returning old ones
    "ursalunaL", "dipplin", "poltchageist", "sinistcha", "okidogi",
    "munkidori", "fezandipiti", "ogerpon", "ogerponFc", "ogerponFn",
    "ogerponP",
}
-- Checks if a Pokémon exists in a given gen 9 game
p.existsInGame = function(poke, game)
    if game == "SV" then
        return not tab.search(pokesSV2, poke)
    -- elseif game == "SV-2" then
    --     return true
    else
        return true
    end
end

-- ====================== "Decompress" PokéMoves entries ======================
-- Decompress a level entry. A level entry is the "table" obtained picking a
-- pokemon, generation and move from pokemoves-data
-- (ie: pokemoves[poke].level[gen][move])
p.decompressLevelEntry = function(entry, gen)
    local res
    if type(entry) == 'table' then
        res = tab.copy(entry)
    else
        res = { { entry } }
    end
    if #res == 1 then
        res = tab.map(p.games.level, function()
            return tab.copy(res[1])
        end)
    end
    return res
end

--[[

Add header and footer for a learnlist table.
Arguments:
    - body: body of the learnlist, to enclose between header and footer
    - poke: Pokémon name or ndex
    - gen: the generation of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event".

--]]
p.addhf = function(body, poke, gen, kind)
    local name, abbr = formlib.getnameabbr(poke)
    local pokedata = multigen.getGen(pokes[poke], gen)
    -- Interp of concat because the interp data are used twice
    return str.interp(table.concat({
        p.strings.HEADER,
        body,
        p.strings.FOOTER,
    }, "\n"), {
        -- "{{#invoke: learnlist-hf | ${kind}${hf} | ${poke} | ${type1} | ${type2} | ${genh} | ${genp} }}",
        kind = kind,
        poke = pokedata.name,
        type1 = pokedata.type1,
        type2 = pokedata.type2,
        genh = gen,
        genp = (abbr ~= "base" and abbr ~= "") and genlib.getGen.game(altdata[name].since[abbr])
               or genlib.getGen.ndex(pokedata.ndex),
    })
end

--[[

General function to build a call.

Arguments:
    - poke: Pokémon name or ndex
    - game: the game of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event". Also used to select functions (picks the funcDict)

--]]
p.entryGeneric = function(poke, game, kind)
    local pmkind = pokemoves[poke][kind]

    local funcDict = p.dicts[kind]
    local res = {}
    if pmkind and pmkind[gen] and not p.alltm(kind, pmkind[gen]) then
        res = funcDict.dataMap(pmkind[gen], function(v, k)
            return funcDict.processData(poke, gen, game, v, k)
        end)
    end
    local resstr
    if #res == 0 then
        resstr = p.strings.NULLENTRY
    elseif pmkind and pmkind[gen] and p.alltm(kind, pmkind[gen]) then
        resstr = "TODO"
    else
        table.sort(res, funcDict.lt)
        resstr = wlib.mapAndConcat(res, "\n", function(val)
            return funcDict.makeEntry(poke, gen, game, val)
        end)
        resstr = table.concat({
            p.strings.ENTRYHEAD,
            resstr,
            p.strings.ENTRYFOOT,
        }, "\n")
    end

    return p.addhf(resstr, poke, gen, kind)
end

-- Fixing dicts
p.dicts = learnlist.dicts

-- ================================== Level ==================================
p.dicts.level = {
    processData = function(poke, gen, game, levels, move)
        levels = p.decompressLevelEntry(levels, gen)
        -- levels = { {"inizio"}, {"inizio", "evo"} },
        local gameidx = tab.search(p.games.level, game)
        assert(gameidx, "game not found")
        return tab.map(levels[gameidx], function(lvl)
            return { move, lvl }
        end)
    end,
    dataMap = tab.flatMapToNum,
    -- elements of res are like
    -- { <movename>, <level> }
    lt = function(a, b)
        return a[2] == b[2] and a[1] < b[1] or learnlist.ltLevel(a[2], b[2])
    end,
    --[[
    makeEntry: create the string of an entry from an element produced by processData.
        Takes three arguments:
            - poke: Pokémon name or ndex
            - gen: the generation of this entry
            - game: the game of this entry
            - entry: the element produced by processData
    --]]
    makeEntry = function(poke, gen, game, entry)
        local move = entry[1]
        return str.interp(p.strings.ENTRIES.level, {
            move = multigen.getGenValue(moves[move].name, gen),
            STAB = p.computeSTAB(poke, move, nil, gen),
            notes = "",
            level = str.fu(entry[2]),
        })
    end
}

-- ==================================== Tm ====================================
p.dicts.tm = {
    processData = function(poke, gen, game, move)
        local kind, num = learnlist.getTMNum(move, gen)
        return { move, kind, num }
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, <kind>, <num> }
    -- num is a string
    lt = function(a, b)
        if a[1] == b[2] then
            -- They are the same element, hence a < b is false
            return false
        end
        -- "kind" are already sorted alfabetically
        return a[2] > b[2]
            or (a[2] == b[2] and tonumber(a[3]) < tonumber(b[3]))
    end,
    makeEntry = function(poke, gen, game, entry)
        local move = entry[1]
        -- { <movename>, <kind>, <num> }
        return str.interp(p.strings.ENTRIES.tm, {
            move = multigen.getGenValue(moves[move].name, gen),
            STAB = p.computeSTAB(poke, move, nil, gen),
            notes = "",
            tmnum = table.concat{ entry[2], entry[3] },
        })
    end
}

-- ================================== Breed ==================================
p.dicts.breed = {
    processData = function(poke, gen, game, movedata, move)
		-- If the Pokémon can learn the move via level, drops it since it
		-- means the breed is a remnant of preevos.
		-- For instance, Abra has Confusione listed via breed, but its evos
		-- learn it via level
		if learnlist.learnKind(move, poke, gen, "level") then
			return nil
		end
        -- If the current game is among the games the Pokémon can learn the
        -- move in, we keep it
        if not movedata.games or tab.search(movedata.games, game) then
            return move
        else
            return nil
        end
    end,
    dataMap = tab.mapToNum,
    -- elements of res are just
    -- <movename>
    lt = function(a, b)
        return a < b
    end,
    makeEntry = function(poke, gen, game, move)
        -- val :: <movename>
        return str.interp(p.strings.ENTRIES.breed, {
            move = multigen.getGenValue(moves[move].name, gen),
            STAB = p.computeSTAB(poke, move, nil, gen),
            notes = "",
        })
    end
}

-- ================================== Preevo ==================================
local function makePreevoPoke(pair)
    local t = { str.tf(pair[1]), "|" }
    if pair[2] then
        table.insert(t, pair[2])
        table.insert(t, "|")
    end
    return table.concat(t)
end

p.dicts.preevo = {
    processData = function(poke, gen, game, preevos, move)
        return { move, tab.map(preevos, function(ndex)
            return { ndex, "" }
        end, ipairs), games = preevos.games }
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, { <array of preevo pairs: { ndex, notes }> }, games = <some list of games?> }
    lt = function(a, b)
        return a[1] < b[1]
    end,
    makeEntry = function(poke, gen, game, val)
        local move = val[1]
        local preevos = val[2]

        if #preevos < 1 or #preevos > 2 then
            print("-------------> ERROR")
            return "-------------> ERROR"
        end
        return str.interp(p.strings.ENTRIES.preevo, {
            move = multigen.getGenValue(moves[move].name, gen),
            STAB = p.computeSTAB(poke, move, nil, gen),
            poke1 = makePreevoPoke(preevos[1]),
            poke2 = preevos[2] and makePreevoPoke(preevos[2]) or "",
        })
    end
}


p.level = function(poke, game)
    return p.entryGeneric(poke, game, "level")
end
p.tm = function(poke, game)
    return p.entryGeneric(poke, game, "tm")
end
p.breed = function(poke, game)
    return p.entryGeneric(poke, game, "breed")
end
p.preevo = function(poke, game)
    return p.entryGeneric(poke, game, "preevo")
end

return p
