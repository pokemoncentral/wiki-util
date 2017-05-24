--[[
--]]
-- Needed to load utility Wiki modules
package.path = package.path .. ';../modules/?.lua'

local txt = require('Wikilib-strings')
local alt = require('AltForms-data')
local useless = require('UselessForms-data')

local makeDictPage = require('dictPage')

io.output(arg[1])

local makeRedirects = function(data, ndex)
	for abbr in pairs(data.names) do
		if abbr ~= 'base' then
			local title = string.interp('File:Ani${ndex}${abbr}MS.gif',
				{ndex = ndex, abbr = abbr})
			local content = string.interp('#RINVIA [[File:${ndex}${abbr}MS.png]]',
				{ndex = ndex, abbr = abbr})
			io.write(makeDictPage(title, content))
		end
	end
end

for poke, data in pairs(alt) do
	local ndex = tonumber(poke)
	if ndex then
		makeRedirects(data, string.tf(ndex))
	end
end

for poke, data in pairs(useless) do
	local ndex = tonumber(poke)
	if ndex then
		makeRedirects(data, string.tf(ndex))
	end
end
