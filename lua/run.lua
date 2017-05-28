--[[

This script is meant as an entry point
for all the other ones: it adds the
path to Scribunto-equivalent modules to
package.path and then runs the provided
script.

--]]

local config = require('config')
package.path = table.concat{
	package.path,
	';',
	config.modulesPath,
	'/?.lua'
}

--[[
	gsub is used to strip the lua extension,
	so that you can use shell autocompletion.
--]]
require((table.remove(arg, 1):gsub('%.lua', '')))
