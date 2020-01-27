# wiki-util
Utility code to serve Pokémon Central Wiki purposes

## Configuration and running

Configuration files are specific to every user, so
they are purposely in the .gitignore; templates are
provided in the config-templates directory though.
Every directory has two noticeable files, with an
appropriate extension:
-	_config.*_: contains the configuration for the
		current type of scripts,
-	_run.*_: loads the configuration properly and
		runs the passed script, comprising command
		line arguments.

# Dependencies

## Bash
-	[pywikibot](https://www.mediawiki.org/wiki/Manual:Pywikibot)
-	[imagemagick](https://www.imagemagick.org/script/index.php)
-	[gifsicle](https://www.lcdf.org/gifsicle/)
-	[uni2ascii](https://billposer.org/Software/uni2ascii.html)

## Lua
-	[wiki-modules](https://github.com/pokemoncentral/wiki-lua-modules)
