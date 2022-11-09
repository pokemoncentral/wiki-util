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
local ex8 = require("learnlist-gen.existence8-data")

p.strings = {
    HF = "{{#invoke: Learnlist/hf | ${kind}${hf} | ${poke} | ${type1} | ${type2} | ${genh} | ${genp} }}",
    NULLENTRY = "{{#invoke: Learnlist/entry9 | ${kind}null}}",
    ENTRYHEAD = "{{#invoke: render | render | Modulo:Learnlist/entry9 | ${kind} | //",
    ENTRYFOOT = "}}",
    ENTRIES = {
        level = "|${move}|${STAB}|${notes}|${levelSV}| //",
        tm = "|${move}|${STAB}|${notes}|${tmnumSV}| //",
        breed = "|${parents}|${move}|${STAB}|${notes}| //",
        tutor = "|${move}|${STAB}|${notes}|${svyn}| //",
        preevo = "|${move}|${STAB}|${poke1}${poke2} //",
    }
}
p.strings.HEADER = str.interp(p.strings.HF, { hf = "h" })
p.strings.FOOTER = str.interp(p.strings.HF, { hf = "f" })

--[[

Local computeSTAB function, that puts "no" when needed instead of relying on
autocompute (that can be wrong for instance for alternative forms).

--]]
p.computeSTAB = function(ndex, movename, form, gen)
    local stab = learnlib.computeSTAB(ndex, movename, form, gen)
    return stab == "" and "no" or stab
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

Internal function of genericEntry. Used when taking data not from the data
module (ie: learnlist after base SV)

Arguments:
    - poke: Pokémon name or ndex
    - gen: the generation of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event". Also used to select functions (picks the funcDict)
    - pmkind: the (possibly fake) entry of the data module

--]]
p._entryGeneric = function(poke, gen, kind, pmkind)
    local funcDict = p.dicts[kind]
    local res = {}
    if pmkind and pmkind[gen] then
        res = funcDict.dataMap(pmkind[gen], function(v, k)
            return funcDict.processData(poke, gen, v, k)
        end)
    end
    local resstr
    if #res == 0 then
        resstr = p.strings.NULLENTRY
    else
        table.sort(res, funcDict.lt)
        resstr = wlib.mapAndConcat(res, "\n", function(val)
            return funcDict.makeEntry(poke, gen, val)
        end)
        resstr = table.concat({
            p.strings.ENTRYHEAD,
            resstr,
            p.strings.ENTRYFOOT,
        }, "\n")
    end

    return p.addhf(resstr, poke, gen, kind)
end

--[[

General function to build a call. Copied from Learnlist module.

Arguments:
    - poke: Pokémon name or ndex
    - gen: the generation of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event". Also used to select functions (picks the funcDict)

--]]
p.entryGeneric = function(poke, gen, kind)
    local pmkind = pokemoves[poke][kind]

    return p._entryGeneric(poke, gen, kind, pmkind)
end

-- Fixing dicts (just printing)
p.dicts = learnlist.dicts

do
    local oldprocessData = learnlist.dicts.level.processData
    p.dicts.level.processData = function(poke, gen, levels, move)
        levels = learnlist.decompressLevelEntry(levels, gen)
        -- If there is only one level in each game for the move, just puts them all
        -- in a single row, otherwise multiple rows
        if tab.all(levels, function(v) return #v == 1 end) then
            return { { move, tab.map(levels, function(t) return t[1] end) } }
        end
        return oldprocessData(poke, gen, levels, move)
    end
end

--[[

makeEntry: create the string of an entry from an element produced by processData.
    Takes three arguments:
        - poke: Pokémon name or ndex
        - gen: the generation of this entry
        - entry: the element produced by processData

--]]
p.dicts.level.makeEntry = function(poke, gen, pair)
    local move, levels = pair[1], pair[2]
    if #levels ~= 1 then
        print("-------------> ERROR")
        return "-------------> ERROR"
    end
    return str.interp(p.strings.ENTRIES.level, {
        move = multigen.getGenValue(moves[move].name, gen),
        STAB = p.computeSTAB(poke, move, nil, gen),
        notes = "",
        levelSV = levels[1] and str.fu(levels[1]) or "no",
    })
end

p.dicts.tm.makeEntry = function(poke, gen, val)
    local move = val.move
    -- { move: <movename>, <array of { <games abbr>, <kind>, <num> }> }

    if #val ~= 1 then
        print("-------------> ERROR")
        return "-------------> ERROR"
    end
    return str.interp(p.strings.ENTRIES.tm, {
        move = multigen.getGenValue(moves[move].name, gen),
        STAB = p.computeSTAB(poke, move, nil, gen),
        notes = "",
        tmnumSV = val[1][2] and table.concat{ val[1][2], val[1][3] } or "no",
    })
end

p.dicts.tutor.makeEntry = function(poke, gen, val)
    -- val :: { <movename>, { <array of games pairs { <abbr>, "Yes"/"No" }> } }
    local move = val[1]
    local gamesarray = val[2]

    if #gamesarray ~= 1 then
        print("-------------> ERROR")
        return "-------------> ERROR"
    end
    -- return "-------------> ERROR2"
    return str.interp(p.strings.ENTRIES.tutor, {
        move = multigen.getGenValue(moves[move].name, gen),
        STAB = p.computeSTAB(poke, move, nil, gen),
        notes = "",
        svyn = gamesarray[1][2]:lower(),
    })
end

p.dicts.breed.makeEntry = function(poke, gen, val)
    -- val :: { <movename>, { <array of parents> }, <notes>, games = <sigla or nil> }
    local move = val[1]
    local parents = val[2]

    local notes = val[3]
    if val.games then
        -- Add games as a separate note, so that they appear as sup
        if notes == "" then
            notes = table.concat(val.games)
        else
            notes = table.concat{ notes, "|", table.concat(val.games) }
        end
    end

    if #parents == 0 then
        print("-------------> ERROR")
        return "-------------> ERROR"
    end
    parents = wlib.mapAndConcat(parents, function(ndex)
        ndex = type(ndex) == "number" and str.tf(ndex) or ndex
        return table.concat{ "#", ndex, "#" }
    end)

    return str.interp(p.strings.ENTRIES.breed, {
        move = multigen.getGenValue(moves[move].name, gen),
        STAB = p.computeSTAB(poke, move, nil, gen),
        notes = notes,
        parents = parents,
    })
end

local function makePreevoPoke(pair)
    local t = { str.tf(pair[1]), "|" }
    if pair[2] then
        table.insert(t, pair[2])
        table.insert(t, "|")
    end
    return table.concat(t)
end

p.dicts.preevo.makeEntry = function(poke, gen, val)
    -- val :: { <movename>, { <array of preevo pairs { ndex, notes }> } }
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


p.level = function(poke)
    return p.entryGeneric(poke, 9, "level")
end
p.tm = function(poke)
    return p.entryGeneric(poke, 9, "tm")
end
p.breed = function(poke)
    return p.entryGeneric(poke, 9, "breed")
end
p.tutor = function(poke)
    return p.entryGeneric(poke, 9, "tutor")
end
p.preevo = function(poke)
    return p.entryGeneric(poke, 9, "preevo")
end

return p
