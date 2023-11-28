--[[

Library for lua files used in pokemoves-autogen

--]]

local lib = {}

-- luacheck: globals tempoutdir pokemoves
require('source-modules')(true)
local tab = require('Wikilib-tables')
local tmdata = require("Machines-data")

-- copy of Wikilib-learnlists.games
lib.games = {
    level = {
        { "RB", "G" },
        { "OA", "C" },
        { "RZ", "RFVF", "S" },
        { "DP", "Pt", "HGSS" },
        { "NB", "N2B2" },
        { "XY", "ROZA" },
        { "SL", "USUL" },
        { "SpSc", "DLPS" },
        { "SV", "SV-2" },
    },
    -- TODO make effective this table, right now only gen 8 is used
    tm = { {}, {}, {}, {}, {}, {}, {}, { "SpSc", "DLPS" }, { "SV", "SV-2" } },
    breed = {
        {},
        { "OA", "C" },
        { "RZ", "RFVF", "S" },
        { "DP", "Pt", "HGSS" },
        { "NB", "N2B2" },
        { "XY", "ROZA" },
        { "SL", "USUL" },
        { "SpSc", "DLPS" },
        { "SV", "SV-2" },
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
        { },
    },
    preevo =  { {}, {}, {}, {}, {}, {}, {}, { "SpSc", "DLPS" }, { "SV", "SV-2" } },
}

--[[

Given a move, an ndex, a gen and a kind check whether that Pokémon can learn
that move in that generation in that kind. Return a true value if it can, a
false otherwise.
Arguments:
	- move: name of the move
	- ndex: name or ndex of the Pokémon
	- gen: generation (a string)
	- kind: kind of learnlist ("level", "tm", ...)

--]]
lib.learnKind = function(move, ndex, gen, kind)
    local pmkind = pokemoves[ndex][kind]
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

--[[

Given a move and an ndex check whether that Pokémon can learn the given move
in a given generation. Return a true value if it can, a false otherwise. It is
also possible to give an array of kind that aren't considered when determining
whether it can learn the move or not.
Arguments:
	- move: name of the move
	- ndex: name or ndex of the Pokémon
	- gen: generation
	- excludekinds: (optional) array of kinds to exclude

--]]
lib.canLearn = function(move, ndex, gen, excludekinds)
	excludekinds = excludekinds or {}
	return tab.any(pokemoves[ndex], function(_, kind)
		if tab.search(excludekinds, kind) then
			return false
		end
		return lib.learnKind(move, ndex, gen, kind)
	end)
end

--[[

Computes the list of moves that a Pokémon can learn in any way, possibly
excluding some kinds.
Arguments:
        - ndex: name or ndex of the Pokémon
        - gen: generation to compute the list for
        - excludekinds: (optional) an array of kinds to esclude from the list. For
                        instance, if this argument is { "breed" } moves that the
                                        Pokémon can only learn by breed aren't included.
Return an array of move names.

--]]
lib.learnset = function(ndex, gen, excludekinds)
    local movedata = pokemoves[ndex]
    excludekinds = excludekinds or {}
    local res = {}
    -- if movedata.tm[gen] and not tab.search(excludekinds, "tm") then
    --     res = tab.copy(movedata.tm[gen])
    --     table.insert(excludekinds, "tm")
    -- end

    for kind, data in pairs(movedata) do
        if not tab.search(excludekinds, kind) and data[gen] then
            res = tab.merge(res, tab.keys(data[gen]))
        end
    end
    return tab.unique(res)
end

--[[

Check whether a a Pokémon can learn a move in a generation previous than the
given one. If it can't returns false, otherwise the highest generation in which
it can  learn it.
Arguments:
	- move: name of the move
	- ndex: name or ndex of the Pokémon
	- gen: the gen considered: the function controls any generation strictly
	       lower than this.
	- firstgen: (optional) the lowest gen to check. Defaults to 1

--]]
lib.learnPreviousGen = function(move, ndex, gen, firstgen)
	for g = gen - 1, firstgen or 1, -1 do
		if tab.any(pokemoves[ndex], function(_, kind)
			return lib.learnKind(move, ndex, g, kind)
		end) then
			return g
		end
	end
	return false
end

-- Get the ndex from a key, that is either a number or a string. If it's a
-- string, it may be an ndex followed by an abbr or a name. If the key is an
-- ndex (possibly with an abbr) returns the numeric ndex, otherwise nil
lib.getNdex = function(poke)
	if type(poke) == "number" then
		return poke
	end
	return type(poke) == "string" and tonumber(poke:match("%d+")) or nil
end

return lib
