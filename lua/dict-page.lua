--[[

This module contains a function building
a page in default pagefromfile pywikibot
format, and a convenience version for
redirects. When invoked directly, the
first one is called.

--]]

--[[

Allowing direct callers to invoke the
generic dict-building function

--]]
local dict = setmetatable({}, {
    __call = function(this, ...)
        return this.dict(...)
    end
})

-- The generic dict-building function
dict.dict = function(title, content)
	return table.concat{
		'{{-start-}}\n',
		"'''", title, "'''\n",
		content,
		'\n{{-stop-}}\n'
	}
end

-- Convenience redirect builder
dict.redirect = function(source, dest)
    return dict.dict(dest, table.concat{
        '#RINVIA[[', source, ']]'})
end

return dict
