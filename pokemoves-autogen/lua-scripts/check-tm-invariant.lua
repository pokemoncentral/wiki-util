#!/usr/bin/lua
--[[

Check the tm invariant, that is the fact that if a Pokémon can learn a move via
TM in a generation it can learn it in ALL games of that generation in which
that move is a tm.

For instance: suppose the move "Azione" is a TM in SpSc and in DLPS, and that
Bulbasaur can learn Azione via TM in SpSc. Then the invariant is uphold if
Bulbasaur also learns Azione via TM in DLPS. Conversely, if Semebomba is a TM
in SpSc but not in DLPS, then the invariant is always valid: since Semebomba is
a TM only in SpSc in gen 8, either Bulbasaur can learn it via TM in all games
in which is a TM (ie. only SpSc) or in none.

--]]

-- luacheck: globals tempoutdir
require('source-modules')

require('dumper')
-- luacheck: globals DataDumper

local tab = require('Wikilib-tables')
local str = require('Wikilib-strings')
local lib = require('Wikilib-learnlists')

local function ParseCSVLine(line,sep)
	local res = {}
	local pos = 1
	sep = sep or ','
	while true do
		local c = string.sub(line,pos,pos)
		if (c == "") then break end
		if (c == '"') then
			-- quoted value (ignore separator within)
			local txt = ""
			repeat
				local startp,endp = string.find(line,'^%b""',pos)
				txt = txt..string.sub(line,startp+1,endp-1)
				pos = endp + 1
				c = string.sub(line,pos,pos)
				if (c == '"') then txt = txt..'"' end
				-- check first char AFTER quoted string, if it is another
				-- quoted string without separator, then append it
				-- this is the way to "escape" the quote char in a quote. example:
				--   value1,"blub""blip""boing",value3  will result in blub"blip"boing  for the middle
			until (c ~= '"')
			table.insert(res,txt)
			assert(c == sep or c == "")
			pos = pos + 1
		else
			-- no quotes used, just look for the first separator
			local startp,endp = string.find(line,sep,pos)
			if (startp) then
				table.insert(res,string.sub(line,pos,startp-1))
				pos = endp + 1
			else
				-- no separator found -> use rest of string and terminate
				table.insert(res,string.sub(line,pos))
				break
			end
		end
	end
	return res
end

local libgamestm = {
	[8] = { "SpSc", "DLPS" }
}

local data = { [8] = {} }

local poke = str.trim(arg[1]) or "staraptor"

local outfile = io.open(tempoutdir .. "/luamoves/" .. poke .. ".lua", "w")

for line in io.lines(tempoutdir .. "/pokecsv/" .. poke .. ".csv") do
	line = tab.map(ParseCSVLine(line), str.trim)
	local kind = line[2]
	local gen = tonumber(line[3])
	local move = line[1]
	if gen >= 8 and kind == "tm" and poke ~= "mew" then
		local tmgames = libgamestm[gen]
		data[gen][move] = data[gen][move]
						  or tab.map(tmgames, function(game)
							return lib.getTMNum(move, gen, game) == nil and "NP" or "NL"
						  end)
		data[gen][move][tab.search(tmgames, line[4])] = "L"
	end
end

-- Now checks data
-- print(DataDumper(data))
for gen, moves in pairs(data) do
	for move, v in pairs(moves) do
		if not table.all(v, function(a) return a == "NP" or a == "L" end) then
			-- print("ERROR")
			-- print(poke, move, gen)
			-- print(DataDumper(v, move))
			print(poke)
			os.exit(1)
		end
	end
end

-- print("Ok")
return 0