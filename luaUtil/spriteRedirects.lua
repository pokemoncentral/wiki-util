--[[

This script creates sprite redirects
from a game to another for a certain
category of Pokémon.

The output is stored in the supplied
file name in a format that is
understandable by pagefromfile
pywikibot script.

Parameters:
	- 1: Output file name
	- 2: source sprite game
	- 3: destination sprite game
	- 4: category for which create redirects. One of:
		- females (all Pokémon that have different genders sprites)
		- mega
		- megax
		- megay
		- archeo

--]]

-- Needed to load utility Wiki modules
package.path = package.path .. ';../modules/?.lua'

local tab = require('Wikilib-tables')
local txt = require('Wikilib-strings')
local forms = require('AltForms-data')
local data = require('Wikilib-data')
local pokes = require('Poké-data')

--[[
	Holds data for various categories of Pokémon:
	these include the list of Pokémon in the
	category, the sex and the form abbreviation.
--]]
local sources = {}
sources.females = {pokes = data.alsoFemales, sex = 'f', form = ''}
sources.mega = {pokes = forms.mega, sex = 'm', form = 'M'}
sources.megax = {pokes = forms.megaxy, sex = 'm', form = 'MX'}
sources.megay = {pokes = forms.megaxy, sex = 'm', form = 'MY'}
sources.archeo = {pokes = forms.archeo, sex = 'm', form = 'A'}

-- Prints to std output a file name of a sprite
local printFileName = function(prefix, game, variant, ndex,
		form, ext)
	io.write('File:', prefix, game, variant, ndex, form,
			'.', ext)
end

-- Prints the pywikibot redirect syntax to std output
local printRedirect = function(fromGame, toGame, prefix,
		variant, ndex, form, ext)
	io.write("{{-start-}}\n'''")
	printFileName(prefix, toGame, variant, ndex, form, ext)
	io.write("'''\n#RINVIA[[")
	printFileName(prefix, fromGame, variant, ndex, form, ext)
	io.write(']]\n{{-stop-}}\n')
end

io.output(io.open(arg[1], 'a'))

local fromGame, toGame, source = arg[2], arg[3], sources[arg[4]]

for k, poke in ipairs(source.pokes) do
	if type(poke) == 'string' then
		local tfNdex = string.tf(pokes[poke].ndex)
		local sex = table.search(data.onlyFemales, poke)
				and 'f' or source.sex

		io.write(pokes[poke].name, '\n\n')

		-- Base redirect
		printRedirect(fromGame, toGame, 'Spr', sex,
				tfNdex, source.form, 'gif')

		-- Shiny redirect
		printRedirect(fromGame, toGame, 'Spr', sex .. 'sh',
				tfNdex, source.form, 'gif')

		io.write('\n')
	end
end

io.close()
