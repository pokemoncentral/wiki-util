local modulesPath = arg[2] or '../modules'

package.path = table.concat{
	package.path,
	';',
	modulesPath,
	'/?.lua'
}

require((arg[1]:gsub('%.lua', '')))
