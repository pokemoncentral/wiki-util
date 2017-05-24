--[[

This script writes to a file whether
a list of sprites has some form missing,
including gender differences, in a
given generation.

Parameters:
	- 1: output file name
	- 2: the generation of files, to be
			able to check only for forms
			existent at that time
	- 3-onwards: input sprite file names

--]]

-- Needed to load utility Wiki modules
package.path = package.path .. ';../modules/?.lua'

local tab = require('Wikilib-tables')
local gens = require('Wikilib-gens')
local alsoFemales = require('Wikilib-data').alsoFemales
local altForms = require('AltForms-data')
local uselessForms = require('UselessForms-data')

local outFile = table.remove(arg, 1)
local gen = tonumber(table.remove(arg, 1))
local spriteNames = table.concat(arg, ' ')

io.output(outFile)

for ndexTf in spriteNames:gmatch('%d+') do
	local ndex = tonumber(ndexTf)

	--[[
		Every Pokémon has at leas one form.
		Also, before fourth gen gender
		differences didn't exist.
	--]]
	local formsCount = (gen > 3 and table.search(alsoFemales,
			ndex)) and 2 or 1
	

	local alt = altForms[ndex] or uselessForms[ndex]
	if alt then
		for form, game in pairs(alt.since) do
			if form ~= 'base' and gens.getGen.game(game) <= gen then
				formsCount = formsCount + 1
			end
		end
	end

	if formsCount > 1 then
		local _, altSpritesCount = spriteNames:gsub(ndexTf, '')
		if altSpritesCount < formsCount then
			io.write('Some alternative forms sprites missing for ',
					ndexTf, '\n')
		end
	end
end
