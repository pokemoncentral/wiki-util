--[[

Utils for print-learnlist-n with n >= 9

--]]
-- luacheck: globals pokemoves tempoutdir
require('source-modules')

local l = {}

local str = require("Wikilib-strings")
local tab = require("Wikilib-tables")
local learnlib = require("Wikilib-learnlists")
local scriptslib = require("lua-scripts.lib")
local wlib = require('Wikilib')
local pokemoves = require("learnlist-gen.pokemoves-data")
-- local genlib = require('Wikilib-gens')
-- local multigen = require('Wikilib-multigen')
-- local formlib = require('Wikilib-forms')
-- local learnlist = require('learnlist-gen.learnlist')
-- local moves = require("Move-data")
-- local pokes = require("Poké-data")
-- local altdata = require("AltForms-data")


-- Get the list of games by kind for the given generation
l.getGames = function(gen)
    return tab.map(scriptslib.games, function(lst)
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

l.learnKind = scriptslib.learnKind

-- Checks whether the entry is alltm
l.isAlltm = function(kind, pmkindgen)
    return kind == "tm" and pmkindgen.all
end

-- Identity function
l.id = function(x) return x end

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

-- ====================== "Decompress" PokéMoves entries ======================
-- Decompress a level entry. A level entry is the "table" obtained picking a
-- pokemon, generation and move from pokemoves-data
-- (ie: pokemoves[poke].level[gen][move])
l.decompressLevelEntry = function(entry, gen)
	local res
	if type(entry) == 'table' then
		res = tab.copy(entry)
	else
		res = { { entry } }
	end
	if #res == 1 then
		res = tab.map(scriptslib.games.level[gen], function()
			return tab.copy(res[1])
		end)
	end
	return res
end

-- ================================== Level ==================================
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
-- and the second contains corresponding contents of the tabs. The third
-- parameter is a function to know whether the current index is active
l.putInTabs = function(titles, contents, isActive)
    return table.concat({
        TABS_STRINGS.HEADER,
        wlib.mapAndConcat(titles, function(title, n)
            return str.interp(TABS_STRINGS.HEADERITEM, {
                n = n,
                title = title,
                active = isActive(n) and TABS_STRINGS.ACTIVE or "",
            })
        end, "\n"),
        TABS_STRINGS.BODY,
        wlib.mapAndConcat(contents, function(content, n)
            return str.interp(TABS_STRINGS.ITEM, {
                n = n,
                content = content,
                active = isActive(n) and TABS_STRINGS.ACTIVE or "",
            })
        end, "\n"),
        TABS_STRINGS.FOOTER,
    }, "\n")
end

return l
