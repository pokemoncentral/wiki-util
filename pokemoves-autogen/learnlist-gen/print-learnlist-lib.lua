--[[

Utils for print-learnlist-n with n >= 9

--]]
-- luacheck: globals tempoutdir
require("source-modules")(false)

package.path = package.path
    .. ";/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-util/pokemoves-autogen/learnlist-gen/require-fallback.lua"

local l = {}

local str = require("Wikilib-strings")
local tab = require("Wikilib-tables")
local learnlib = require("Wikilib-learnlists")
-- local scriptslib = require("lua-scripts.lib")
local wlib = require("Wikilib")

-- copy of Wikilib-learnlists.games
l.games = {
    level = {
        { "RB", "G" },
        { "OA", "C" },
        { "RZ", "RFVF", "S" },
        { "DP", "Pt", "HGSS" },
        { "NB", "N2B2" },
        { "XY", "ROZA" },
        { "SL", "USUL" },
        { "SpSc", "DLPS" },
        { "SV", "SV-2", "SV-3" },
    },
    tm = {
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        { "SpSc", "DLPS" },
        { "SV", "SV-2", "SV-3" },
    },
    breed = {
        {},
        { "OA", "C" },
        { "RZ", "RFVF", "S" },
        { "DP", "Pt", "HGSS" },
        { "NB", "N2B2" },
        { "XY", "ROZA" },
        { "SL", "USUL" },
        { "SpSc", "DLPS" },
        { "SV", "SV-2", "SV-3" },
    },
    tutor = {
        {},
        { "C" },
        { "RFVF", "S", "XD" },
        { "DP", "Pt", "HGSS" },
        { "NB", "N2B2" },
        { "XY", "ROZA" },
        { "SL", "USUL" },
        { "SpSc", "IA", "DLPS" },
        {},
    },
    preevo = {
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        { "SpSc", "DLPS" },
        { "SV", "SV-2", "SV-3" },
    },
}

l.requirepm = function(poke)
    return require(tempoutdir .. ".luamoves-final." .. poke)
end

-- Get the list of games by kind for the given generation
l.getGames = function(gen)
    return tab.map(l.games, function(lst)
        return lst[gen]
    end)
end

--[[

Local computeSTAB function, that puts "no" when needed instead of relying on
autocompute (that can be wrong for instance for alternative forms).

--]]
l.computeSTAB = function(ndex, movename, form, gen)
    local stab = learnlib.computeSTAB(ndex, movename, form, gen)
    return stab == "" and "no" or stab
end

-- Re-expose getTMNum
l.getTMNum = learnlib.getTMNum

-- Checks whether the entry is alltm
l.isAlltm = function(kind, pmkindgen)
    return kind == "tm" and pmkindgen.all
end

-- Identity function
l.id = function(x)
    return x
end

-- Check if all elements in a table are equal
l.allEquals = function(t, iter)
    iter = iter or ipairs
    local base
    local started = false
    for _, v in iter(t) do
        if not started then
            base = v
            started = true
        elseif not tab.equal(base, v) then
            return false
        end
    end
    return true
end

--[[

Given a move, an ndex, a gen and a kind check whether that Pokémon can learn
that move in that generation in that kind. Return a true value if it can, a
false otherwise.
Arguments:
    - pmoves: the data for the given pokemon (pokemoves[poke])
	- move: name of the move
	- gen: generation (a string)
	- kind: kind of learnlist ("level", "tm", ...)

--]]
l.learnKind = function(pmoves, move, gen, kind)
    local pmkind = pmoves[kind]
    if not pmkind or not pmkind[gen] then
        return false
    end
    local mdata = pmkind[gen]
    if kind == "tm" and mdata.all then
        return (tab.deepSearch(tmdata[gen], move))
    else
        return mdata[move]
    end
end

-- ====================== "Decompress" PokéMoves entries ======================
-- Decompress a level entry. A level entry is the "table" obtained picking a
-- pokemon, generation and move from pokemoves-data
-- (ie: pokemoves[poke].level[gen][move])
l.decompressLevelEntry = function(entry, gen)
    local res
    if type(entry) == "table" then
        res = tab.copy(entry)
    else
        res = { { entry } }
    end
    if #res == 1 then
        res = tab.map(l.games.level[gen], function()
            return tab.copy(res[1])
        end)
    end
    return res
end

-- ================================== Level ===================================
-- Convert a level (a number, "inizio", "evo", "ricorda" or nil) to a numeric
-- key to make sorting easier
local function levelToNumkey(l)
    if type(l) == "number" then
        return l
    elseif l == nil then
        -- A random big number
        return 999999
    elseif l == "inizio" then
        return -5
    elseif l == "evo" then
        return 0
    elseif l == "ricorda" then
        return -10
    end
    error("unexpected level value")
end

-- Compares two levels (a number, "inizio", "evo", "ricorda" or nil). The order
-- is "ricorda" < "inizio" < "evo" < numbers < nil
l.ltLevel = function(a, b)
    return levelToNumkey(a) < levelToNumkey(b)
end

-- =================================== Preevo =================================
l.makePreevoPoke = function(pair)
    local t = { str.tf(pair[1]), "|" }
    if pair[2] then
        table.insert(t, pair[2])
        table.insert(t, "|")
    end
    return table.concat(t)
end

-- =================================== Tabs ===================================
local TABS_STRINGS = {
    HEADER = "{{Tabs/header|style=border}}",
    HEADERITEM = "{{Tabs/headeritem|n=${n}|title=${title}${active}}}",
    ACTIVE = "|active=yes",
    BODY = "{{Tabs/body}}",
    ITEM = "{{Tabs/item|n=${n}${active}|content=\n${content}\n}}",
    FOOTER = "{{Tabs/footer}}",
}

-- Given a pair of arrays, put them in tabs. The first array contains titles,
-- and the second contains corresponding contents of the tabs
l.putInTabs = function(titles, contents)
    return table.concat({
        TABS_STRINGS.HEADER,
        wlib.mapAndConcat(titles, function(title, n)
            return str.interp(TABS_STRINGS.HEADERITEM, {
                n = n,
                title = title,
                active = n == #titles and TABS_STRINGS.ACTIVE or "",
            })
        end, "\n"),
        TABS_STRINGS.BODY,
        wlib.mapAndConcat(contents, function(content, n)
            return str.interp(TABS_STRINGS.ITEM, {
                n = n,
                content = content,
                active = n == #contents and TABS_STRINGS.ACTIVE or "",
            })
        end, "\n"),
        TABS_STRINGS.FOOTER,
    }, "\n")
end

return l
