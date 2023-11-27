--[[

This file is a library for scripts that prints learnlists for a given Pokémon
in a certain gen. The processing to print such content is always the same, and
only the actual string (the call to that gen module) changes between gen, hence
all the logic can be factored here, leaving only to specify the printing in the
specific file.

TODO: refactor to use oop?

-- ============================================================================

Some useful informations for developers:
    - notes are needed only for breed and preevo
    - except for level and tm, other methods has exactly one line per move.
      A move can be learned at multiple levels, and a tm or hm with a move can
      change within a generation (es: spaccaroccia)

--]]
-- luacheck: globals pokemoves tempoutdir
require('source-modules')

local l = {}

local str = require('Wikilib-strings')
local tab = require('Wikilib-tables')
local lib = require('Wikilib-learnlists')
local genlib = require('Wikilib-gens')
local multigen = require('Wikilib-multigen')
local wlib = require('Wikilib')
local links = require('Links')
local hf = require('Learnlist-hf')
local sup = require("Sup-data")
local pokes = require("Poké-data")
local mtdata = require("Machines-data")
local ex8 = require("learnlist-gen.existence8-data")

-- ============================ Wikilib-learnlists ============================
-- Here are functions previously in Wikilib-learnlists that uses pokemoves-data
-- Moved here to remove dependency on the data module of pages that doesn't use
-- it specifically
local pokemoves = require("learnlist-gen.pokemoves-data")

--[[

Local computeSTAB function, that puts "no" when needed instead of relying on
autocompute (that can be wrong for instance for alternative forms).

--]]
l.computeSTAB = function(ndex, movename, form, gen)
    local stab = lib.computeSTAB(ndex, movename, form, gen)
    return stab == "" and "no" or stab
end

-- Re-expose getTMNum
l.getTMNum = lib.getTMNum

--[[

Given something, compute breed notes, ie. "breed chain", "the parent should
have learned the move in a previous gen" or "no parent can learn the move".
Arguments:
	- gen: the generation of this entry
	- move: the name of the move
	- parent: any parent listed in the data module
	- basenotes (optional): notes from the data module
	                        (ie. pokemoves[poke][kind][gen][move].notes)

BUG: notes are wrong if the Pokémon can learn the move from itself that
learned it in a previous generation, and it is chosen as the parent given
here. Right now, this issue isn't happening because those notes are precomputed

--]]
l.breednotes = function(gen, move, parent, basenotes)
	local notes = { basenotes }
	-- To compute notes it checks only one parent because they should all be
	-- the same for this. Otherwise the different one would be the only one
	-- (for instance: parents that need a chain aren't listed if there are
	-- some that doesn't)

    if gen ~= 9 then
        -- All these notes are not needed in gen 9 (because of picnic)
        if parent and not l.canLearn(move, parent, gen, {"breed"}) then
            if l.learnKind(move, parent, gen, "breed") then
                -- Parent can learn by breed but not in any other way: chain
                table.insert(notes, 1, "catena di accoppiamenti")
            -- In theory this second check is useless because a parent wouldn't
            -- be listed if it doesn't learn the move, so if it doesn't in this
            -- gen it should in a past one
            -- elseif l.learnPreviousGen(move, parent1, gen) then
            else
                table.insert(notes, 1, "il padre deve aver imparato la mossa in una generazione precedente")
            end
        elseif not parent then
            table.insert(notes, 1, "nessun genitore può apprendere la mossa")
        end
    end

	return table.concat(notes, ", ")
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
	-- if type(res[1]) ~= 'table' then
	-- 	res[1] = {res[1]}
	-- end
	if #res == 1 then
		res = tab.map(lib.games.level[gen], function()
			return tab.copy(res[1])
		end)
	end
	return res
end

-- Get a decompressed level entry
l.getLevelEntry = function(move, ndex, gen)
	local pmkind = pokemoves[ndex].level
	if not pmkind or not pmkind[gen] or not pmkind[gen][move] then
		return nil
	end
	return l.decompressLevelEntry(pmkind[gen][move], gen)
end

-- Get the list of games by kind for the given generation
l.filterGames = function(games, gen)
    return tab.map(games, function(lst)
        return lst[gen]
    end)
end

-- ========================== Check learn functions ==========================
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
l.learnKind = function(move, ndex, gen, kind)
	local pmkind = pokemoves[ndex][kind]
	if not pmkind or not pmkind[gen] then
		return false
	end
	local mdata = pmkind[gen]
	if kind == "tm" then
		local mlist = mdata.all and mtdata[gen] or mdata
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
l.canLearn = function(move, ndex, gen, excludekinds)
	excludekinds = excludekinds or {}
	return tab.any(pokemoves[ndex], function(_, kind)
		if tab.search(excludekinds, kind) then
			return false
		end
		return l.learnKind(move, ndex, gen, kind)
	end)
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
l.learnPreviousGen = function(move, ndex, gen, firstgen)
	for g = gen - 1, firstgen or 1, -1 do
		if tab.any(pokemoves[ndex], function(_, kind)
			return l.learnKind(move, ndex, g, kind)
		end) then
			return g
		end
	end
	return false
end


-- ========================== End Wikilib-learnlists ==========================
--[[

Add header and footer for a learnlist table.
Arguments:
    - str: body of the learnlist, to enclose between header and footer
    - poke: Pokémon name or ndex
    - gen: the generation of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event".

--]]
l.addhf = function(str, poke, gen, kind)
    local pokedata = multigen.getGen(pokes[poke], gen)
    local hfargs = { pokedata.name, pokedata.type1, pokedata.type2, gen,
                     genlib.getGen.ndex(pokedata.ndex) }
    return table.concat({
        hf[kind .. "h"]{ args = hfargs },
        str,
        hf[kind .. "f"]{ args = hfargs },
    }, "\n")
end

--[[

General function to build an entry. Requires some functions in funcDict to
determine details of the entry.
Oop isn't used because there's no inheritance.

Arguments:
    - poke: Pokémon name or ndex
    - gen: the generation of this entry
    - kind: kind of entry. Either "level", "tm", "breed", "tutor", "preevo" and
            "event". Also used to select functions (picks the funcDict)

This function makes use of a dictionary of function, retrieved using "kind", to
implement details of the entry. It should contain the following functions:
    - processData: given a single value of pokemoves[poke][kind][gen]
                   transform it in a format more suitable for sorting and
                   printing. It is mapped over that table with dataMap.
                   Takes four arguments:
                    - poke: Pokémon name or ndex
                    - gen: the generation of this entry
                    - value: the value of pokemoves[poke][kind][gen][key]
                    - key: the key of that value
                   It should return an array of elements that will be sorted
                   and printed using other functions in the dict.
    - dataMap: the kind of map used to map processData over the collection.
               Often table.flatMapToNum or table.mapToNum
    - lt: given two elements produced by processData, compares them
          Takes two arguments, the two elements to compare.
    - makeEntry: create the string of an entry from an element produced by
                 processData.
                 Takes three arguments:
                    - poke: Pokémon name or ndex
                    - gen: the generation of this entry
                    - entry: the element produced by processData

--]]
l.entryLua = function(poke, gen, kind)
    local funcDict = l.dicts[kind]

    local res = {}
    local pmkind = pokemoves[poke][kind]
    if pmkind and pmkind[gen] then
        res = funcDict.dataMap(pmkind[gen],
            function(v, k) return funcDict.processData(poke, gen, v, k) end)
    end
    local resstr
    if #res == 0 then
        resstr = lib.entrynull(kind, "100")
    else
        table.sort(res, funcDict.lt)
        resstr = wlib.mapAndConcat(res, "\n", function(val)
            return funcDict.makeEntry(poke, gen, val)
        end)
    end

    return l.addhf(resstr, poke, gen, kind)
end

l.dicts = {}

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

--[[

Comparator for levels. Given two levels tables, that are two arrays of the same
length with each element being either a level (a number, "inizio" or "evo") or
false, it returns true iff a <= b.

Sorting is lexicographic on levels, replacing false with the first subsequent
non-false value.

TODO: make this function more efficient

--]]
l.ltLevelarr = function(a, b)
    for k, v in ipairs(a[2]) do
        local aval, k1 = v, k
        -- Can't use (not aval) because that is true also for nil
        while aval == false do
            k1 = k1 + 1
            aval = a[2][k1]
        end
        local bval, k2 = b[2][k], k
        while bval == false do
            k2 = k2 + 1
            bval = b[2][k2]
        end
        if l.ltLevel(aval, bval) then
            return true
        elseif aval ~= bval then -- if they aren't equale then bval > aval
            return false
        end
    end
    -- here aval == bval at any iteration => equality => check name
    return a[1] < b[1]
end

l.dicts.level = {
    processData = function(poke, gen, levels, move)
        levels = l.decompressLevelEntry(levels, gen)
        -- levels = { {"inizio"}, {"inizio", "evo"} },
        local alllevels = tab.unique(tab.flatten(levels))
        return tab.map(alllevels, function(lvl)
            return { move, tab.map(levels, function(t)
                return tab.search(t, lvl) and lvl or false
            end) }
        end)
    end,
    dataMap = tab.flatMapToNum,
    -- elements of res are like
    -- {
    --     <movename>,
    --    { <level of first game or false>, <level of second game or false>, ... },
    -- }
    lt = l.ltLevelarr,
}

-- ==================================== Tm ====================================
l.dicts.tm = {
    processData = function(poke, gen, move)
        if gen == 8 then
            local out = { move = move }
            for _, game in ipairs(lib.games.tm[gen]) do
                local kind, num = lib.getTMNum(move, gen, game)
                table.insert(out, { game, kind, num })
            end
            -- Check if the Pokémon exists only in SpSc or DLPS, and changes
            -- tms accordingly
            if tab.search(ex8[poke], "SpSc") then
                if not tab.search(ex8[poke], "DLPS") then
                    -- Only SpSc
                    out[2] = out[1]
                end
            elseif tab.search(ex8[poke], "DLPS") then
                -- Only DLPS
                out[1] = out[2]
            end
            return out
        else -- gen <= 7
            local kind, num = lib.getTMNum(move, gen)
            return { move = move, { "", kind, num } }
        end
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { move: <movename>, <array of { <games abbr>, <kind>, <num> }> }
    -- All lists have entries for all games, possibly with kind and num equal
    -- to nil. Num is a string
    lt = function(a, b)
        if a.move == b.move then
            -- They are the same element, hence a < b is false
            return false
        end
        for i, aval in ipairs(a) do
            -- All pairs are guaranteed to be different unless they are both
            -- nil, since if they were equal then the moves would be the same
            -- (because are the same TM in at least one game)
            local bval = b[i]
            if aval[2] and bval[2] then
                -- If both exists can compare right away
                return aval[2] > bval[2]
                        or (aval[2] == bval[2] and tonumber(aval[3]) < tonumber(bval[3]))
            elseif not aval[2] and bval[2] then
                return false
            elseif aval[2] and not bval[2] then
                return true
            end -- else not aval[2] and not bval[2]
            -- In this case, since neither exists, defers comparison to the
            -- next pair
        end
        -- Because sometimes it compares an element with itself
        return false
    end,
}

-- ================================== Breed ==================================
l.dicts.breed = {
    processData = function(poke, gen, movedata, move)
		-- If the Pokémon can learn the move via level, drops it since it
		-- means the breed is a remnant of preevos.
		-- For instance, Abra has Confusione listed via breed, but its evos
		-- learn it via level
		if l.learnKind(move, poke, gen, "level") then
			return nil
		end
        -- Bulba style: in a Pokémon page it prints parents for the latest game
        local parents = lib.moveParentsGame(movedata,
                        lib.games.breed[gen][#lib.games.breed[gen]])

        local notes = movedata.notes or l.breednotes(gen, move, parents[1])
        local res = { move, parents[1] and parents or { 000 }, str.fu(notes),
                      games = movedata.games
                    }
        return res
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, { <array of parents> }, <notes>, games = <sigla or nil> }
    lt = function(a, b)
        return a[1] < b[1]
    end,
}

-- ================================== Tutor ==================================
l.dicts.tutor = {
    processData = function(_, gen, games, move)
        return {
            move,
            tab.zip(lib.games.tutor[gen], games, function(a, b)
                return { a, b and "Yes" or "No" }
            end)
        }
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, { <array of games pairs { <abbr>, "Yes"/"No" }> } }
    lt = function(a, b)
        for k, v in ipairs(a[2]) do
            if v[2] ~= b[2][k][2] then
                -- Equivalent to v[2] < b[2][k][2]
                return v[2] == "Yes"
            end
        end
        return a[1] < b[1]
    end,
}

-- ================================== Preevo ==================================
l.dicts.preevo = {
    processData = function(_, _, preevos, move)
        return { move, tab.map(preevos, function(ndex)
            return { ndex, "" }
        end, ipairs), games = preevos.games }
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, { <array of preevo pairs: { ndex, notes }> } }
    lt = function(a, b)
        return a[1] < b[1]
    end,
}

-- ================================== Event ==================================
l.dicts.event = {
    processData = function(_, _, occasion, move)
        return { move, occasion }
    end,
    dataMap = tab.mapToNum,
    -- elements of res are like
    -- { <movename>, <occasion> }
    lt = function(a, b)
        return a[1] < b[1]
    end,
}

-- ============================================================================
return l
