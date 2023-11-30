--[[

Script to build learnlist-entry calls from pokemoves-data

TODO: support alltm

--]]
-- luacheck: globals tempoutdir
require("source-modules")

local p = {}

local str = require("Wikilib-strings")
local tab = require("Wikilib-tables")
local learnlib = require("Wikilib-learnlists")
local wlib = require("Wikilib")
local genlib = require("Wikilib-gens")
local multigen = require("Wikilib-multigen")
local formlib = require("Wikilib-forms")
local printlib = require("learnlist-gen.print-learnlist-lib")
local moves = require("Move-data")
local pokes = require("Poké-data")
local altdata = require("AltForms-data")

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
    },
}
p.strings.HEADER = str.interp(p.strings.HF, { hf = "h" })
p.strings.FOOTER = str.interp(p.strings.HF, { hf = "f" })

-- Exports for get-learnlist
p.games = printlib.getGames(gen)
-- These should match the order of p.games
p.gameNames = {
    "Ver 1.2.0",
    "Ver 2.0.1",
}
-- 2 is the index of "SV-2"
p.isGameActive = function(num)
    return num == 2
end

p.computeSTAB = printlib.computeSTAB

-- Checks whether the entry is alltm
p.alltm = printlib.isAlltm

-- These Pokémon weren't in SV, and were added in SV-2
-- stylua: ignore
local pokesSV2 = {
    "aipom", "ambipom", "arbok", "ariados", "bellsprout", "chandelure",
    "charjabug", "chimchar", "chimecho", "chingling", "clefable", "clefairy",
    "cleffa", "conkeldurr", "corphish", "cramorant", "crawdaunt", "cutiefly",
    "darkrai", "dipplin", "ducklett", "dusclops", "dusknoir", "duskull",
    "ekans", "empoleon", "feebas", "fezandipiti", "furret", "geodude",
    "geodudeA", "gligar", "gliscor", "golem", "golemA", "graveler",
    "gravelerA", "grotle", "grubbin", "gurdurr", "hakamo-o", "hoothoot",
    "illumise", "infernape", "jangmo-o", "jirachi", "koffing", "kommo-o",
    "lampent", "leavanny", "litwick", "lombre", "lotad", "ludicolo",
    "magcargo", "mamoswine", "manaphy", "mandibuzz", "mienfoo", "mienshao",
    "mightyena", "milotic", "monferno", "morpeko", "munchlax", "munkidori",
    "ninetales", "ninetalesA", "noctowl", "nosepass", "nuzleaf", "ogerpon",
    "okidogi", "phantump", "phione", "piloswine", "piplup", "politoed",
    "poliwag", "poliwhirl", "poliwrath", "poltchageist", "poochyena",
    "prinplup", "probopass", "ribombee", "sandshrew", "sandshrewA",
    "sandslash", "sandslashA", "seedot", "sentret", "sewaddle", "shaymin",
    "shayminC", "shiftry", "sinistcha", "slugma", "snorlax", "spinarak",
    "swadloon", "swanna", "swinub", "timburr", "torterra", "trevenant",
    "turtwig", "victreebel", "vikavolt", "volbeat", "vullaby", "vulpix",
    "vulpixA", "weepinbell", "weezing", "weezingG", "yanma", "yanmega",
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

--[[

Add header and footer for a learnlist table.
Arguments:
    - body: body of the learnlist, to enclose between header and footer
    - poke: Pokémon name or ndex
    - gen: the generation of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event".

--]]
p.addhf = function(body, poke, kind)
    local name, abbr = formlib.getnameabbr(poke)
    local pokedata = multigen.getGen(pokes[poke], gen)

    local genp = (abbr ~= "base" and abbr ~= "")
            and genlib.getGen.game(altdata[name].since[abbr])
        or genlib.getGen.ndex(pokedata.ndex)
    -- Interp of concat because the interp data are used twice
    return str.interp(
        table.concat({
            p.strings.HEADER,
            body,
            p.strings.FOOTER,
        }, "\n"),
        {
            -- "{{#invoke: learnlist-hf | ${kind}${hf} | ${poke} | ${type1} | ${type2} | ${genh} | ${genp} }}",
            kind = kind,
            poke = pokedata.name,
            type1 = pokedata.type1,
            type2 = pokedata.type2,
            genh = gen,
            genp = genp,
        }
    )
end

-- Build a single learnlist call given the preprocessed data
p.makeSingleGameEntry = function(data, poke, kind)
    local funcDict = p.dicts[kind]
    local resstr
    if #data == 0 then
        resstr = p.strings.NULLENTRY
    else
        resstr = wlib.mapAndConcat(data, "\n", function(val)
            return funcDict.makeEntry(poke, gen, game, val)
        end)
        resstr = table.concat({
            p.strings.ENTRYHEAD,
            resstr,
            p.strings.ENTRYFOOT,
        }, "\n")
    end

    return p.addhf(resstr, poke, kind)
end

--[[

General function to make the code for a given Pokémon and kind.

Arguments:
    - poke: Pokémon name or ndex
    - game: the game of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event". Also used to select functions (picks the funcDict)

--]]
p.entryGeneric = function(poke, kind)
    local pmkind = printlib.requirepm(poke)[kind]
    local funcDict = p.dicts[kind]

    -- No data
    if not pmkind or not pmkind[gen] then
        return p.addhf(p.strings.NULLENTRY, poke, kind)
    end

    -- All the interesting games
    local games = tab.filter(p.games[kind], function(game)
        return p.existsInGame(poke, game)
    end)

    local res = {}
    for n, game in ipairs(games) do
        -- Preprocess data to make it more printable
        res[n] = funcDict.dataMap(pmkind[gen], function(v, k)
            return funcDict.processData(poke, gen, game, v, k)
        end)
        table.sort(res[n], funcDict.lt)
    end
    -- Check for equality
    local eqcheck = tab.map(res, funcDict.toGameEqCheck or printlib.id)
    if printlib.allEquals(eqcheck) then
        local data = funcDict.getSingleGameData(res)
        return p.makeSingleGameEntry(data, poke, kind)
    end

    -- Different: print all in tabs
    return printlib.putInTabs(
        p.gameNames,
        tab.map(res, function(r)
            return p.makeSingleGameEntry(r, poke, kind)
        end),
        p.isGameActive
    )
end

p.dicts = {}

-- ================================== Level ==================================
p.dicts.level = {
    processData = function(poke, gen, game, levels, move)
        levels = printlib.decompressLevelEntry(levels, gen)
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
        return a[2] == b[2] and a[1] < b[1] or printlib.ltLevel(a[2], b[2])
    end,
    getSingleGameData = function(res)
        return res[1]
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
    end,
}

-- ==================================== Tm ====================================
p.dicts.tm = {
    processData = function(poke, gen, game, games, move)
        if move == "all" and type(games) == "boolean" then
            return nil
        end
        if tab.search(games, game) then
            local kind, num = printlib.getTMNum(move, gen)
            return { move, kind, num }
        else
            return nil
        end
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, <kind>, <num> }
    -- num is a string
    lt = function(a, b)
        if a[1] == b[1] then
            -- They are the same element, hence a < b is false
            return false
        end
        -- "kind"s are already sorted alfabetically
        return a[2] > b[2] or (a[2] == b[2] and tonumber(a[3]) < tonumber(b[3]))
    end,
    toGameEqCheck = function(data)
        return tab.filter(data, function(entry)
            return tonumber(entry[3]) < 172
        end)
    end,
    getSingleGameData = function(res)
        return res[#res]
    end,
    makeEntry = function(poke, gen, game, entry)
        local move = entry[1]
        -- { <movename>, <kind>, <num> }
        return str.interp(p.strings.ENTRIES.tm, {
            move = multigen.getGenValue(moves[move].name, gen),
            STAB = p.computeSTAB(poke, move, nil, gen),
            notes = "",
            tmnum = table.concat({ entry[2], entry[3] }),
        })
    end,
}

-- ================================== Breed ==================================
p.dicts.breed = {
    processData = function(poke, gen, game, movedata, move)
        -- If the Pokémon can learn the move via level, drops it since it
        -- means the breed is a remnant of preevos.
        -- For instance, Abra has Confusione listed via breed, but its evos
        -- learn it via level
        local pmoves = printlib.requirepm(poke)
        if printlib.learnKind(pmoves, move, gen, "level") then
            return nil
        end
        -- If the current game is among the games the Pokémon can learn the
        -- move in, we keep it
        if not movedata.games or tab.search(movedata.games, game) then
            return { move, movedata.notes or "" }
        else
            return nil
        end
    end,
    dataMap = tab.mapToNum,
    -- elements of res are just
    -- { <movename>, <notes> }
    lt = function(a, b)
        return a[1] < b[1]
    end,
    getSingleGameData = function(res)
        return res[1]
    end,
    makeEntry = function(poke, gen, game, entry)
        -- val :: { <movename>, <notes> }
        return str.interp(p.strings.ENTRIES.breed, {
            move = multigen.getGenValue(moves[entry[1]].name, gen),
            STAB = p.computeSTAB(poke, entry[1], nil, gen),
            notes = entry[2],
        })
    end,
}

-- ================================== Preevo ==================================
p.dicts.preevo = {
    processData = function(poke, gen, game, preevos, move)
        return {
            move,
            tab.map(preevos, function(ndex)
                return { ndex, "" }
            end, ipairs),
            games = preevos.games,
        }
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, { <array of preevo pairs: { ndex, notes }> }, games = <some list of games?> }
    lt = function(a, b)
        return a[1] < b[1]
    end,
    getSingleGameData = function(res)
        return res[1]
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
            poke1 = printlib.makePreevoPoke(preevos[1]),
            poke2 = preevos[2] and printlib.makePreevoPoke(preevos[2]) or "",
        })
    end,
}

return p
