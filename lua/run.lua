--[[

This script is meant as an entry point
for all the other ones: it adds the
path to Scribunto-equivalent modules to
package.path and then runs the provided
script.

--]]

--[[

Since it rarely changes, it's less
convenient to have a command line
parameter for this.

--]]
local MODULES_PATH = ADD_YOUR_PATH_HERE

package.path = table.concat{
	package.path,
	';',
	MODULES_PATH,
	'/?.lua'
}

require((table.remove(arg, 1):gsub('%.lua', '')))
