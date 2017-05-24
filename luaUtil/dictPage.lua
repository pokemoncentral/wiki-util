return function(title, content)
	return table.concat{
		'{{-start-}}\n',
		"'''", title, "'''\n",
		content,
		'\n{{-stop-}}\n'
	}
end
