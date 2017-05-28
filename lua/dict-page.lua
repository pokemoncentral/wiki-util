--[[

This function builds a page in
default pagefromfile pywikibot
format

--]]

return function(title, content)
	return table.concat{
		'{{-start-}}\n',
		"'''", title, "'''\n",
		content,
		'\n{{-stop-}}\n'
	}
end
