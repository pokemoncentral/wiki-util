--[[

Library for lua files used in pokemoves-autogen

--]]

local lib = {}

local txt = require('Wikilib-strings') -- luacheck: no unused
local tab = require('Wikilib-tables')  -- luacheck: no unused
local pokemoves = require("PokéMoves-data")
local tmdata = require("Machines-data")
local learnlib = require('Wikilib-learnlists')

lib.games = learnlib.games

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
	if kind == "tm" then
		local mlist = mdata.all and tmdata[gen] or mdata
		-- Extra parentheses to force a single return value
		return (tab.deepSearch(mlist, move))
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
        if movedata.tm[gen] and not tab.search(excludekinds, "tm") then
                res = tab.copy(movedata.tm[gen])
                table.insert(excludekinds, "tm")
        end

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

return lib