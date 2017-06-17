--[[

This script is meant as an entry point
for all the other ones: it adds the
path to Scribunto-equivalent modules to
package.path and then runs the provided
script.

--]]

local newPath = function(path)
	return table.concat{
		package.path,
		';',
		path,
		'/?.lua'
	}
end

local pathToThis = arg[0]:match('(.+)/.-%.lua$')
package.path = newPath(pathToThis)

local config = require('config')
package.path = newPath(config.modulesPath)

dofile(table.concat{pathToThis, '/', table.remove(arg, 1)})
