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
local scriptFile = table.remove(arg, 1)

if pathToThis then
    package.path = newPath(pathToThis)
    scriptFile = table.concat{pathToThis, '/', scriptFile}
end

local config = require('config')
package.path = newPath(config.modulesPath)

dofile(scriptFile)
