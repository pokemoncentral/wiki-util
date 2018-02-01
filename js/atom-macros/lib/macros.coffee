# All functions defined on "this" are available as atom commands.
#
# If the `toolbar` package is installed, toolbar icons are automatically generated.
#
# Set these properties of your function to configure the icons:
# * icon - name of the icon (Or a method returning the icon name, possibly prepended with 'ion-' or 'fa-')
# * title - The toolbar title (or a method returning the title)
# * hideIcon - set to true to hide the icon from the toolbar
#

###
@summary Converts a wiki module name to its filesystem counterpart.

@param {string} module - The wiki module name.
@return {string} The filesystem name of `module`
###
wiki2fs = (module) ->
    module.replace /^[Mm]odul[oe]:/, ''
        .replace /\//g, '-'

###
@summary Converts a filesystem module name to its wiki counterpart

@param {string} module - The filesystem module name.
@return {string} The filesystem name of `module`
###
fs2wiki = (module) ->
    # Wiki namespaces should only be prepended once.
    namespace = if module.search(/^[Mm]odul[oe]:/) == -1 then 'Modulo:' else ''

    namespace + module.replace /-/g, '/'

###
This function creates a macro of the _filter_ type, that is
a macro that applies some transformations to the text in the
current editor.

@summary Creates a macro of the _filter_ type.

@param {(string) => string} filter - The pure function actually
    performing the transformation.
@return {(void) => void} The macro function, that reads from the
    current editor, applies the transformation and writes back
    into the editor.
###
makeFilterMacro = (filter) ->
    ->
        editor = getActiveTextEditor()
        editor.setText filter editor.getText()

###
This object contains all the _filter_ macros, so that they can
be exported automatically.
###
filterMacros =

    big: (text) ->
        text.replace /<\/big>/gi, '</span>'
            .replace /<big>/gi, '<span class="text-big">'

    colore: (text) ->
        text.replace /\{\{[Cc]olore (\w+?)\}\}/g, '{{#invoke: colore | $1}}'
            .replace /\{\{[Cc]olore (\w+?) (\w+?)\}\}/g, \
                '{{#invoke: colore | $1 | $2}}'

    p: (text) ->
        text

    small: (text) ->
        text.replace /<\/small>/gi, '</span>'
            .replace /<small>/gi, '<span class="text-small">'

    tags: (text) ->
        @big @small text

    ###
    This function transforms the content of a wiki Scribunto
    module into a native Lua source file.

    @summary Transforms Scributo modules into Lua sources.

    @param {string} scribunto - The whole Scribunto source code.
    @return {string} The Lua source corresponding to `scribunto`.
    ###
    toLua: (scribunto) ->
        # Quotes are kept so that the toModule convention for
        # mw.loadData is respected when applying this macros
        # on Lua source code.
        scribunto.replace /require\((["'])(.+?)["']\)/g, (_, quotes, module) ->
                "require(#{ quotes }#{ wiki2fs module }#{ quotes })"

            .replace /mw\.loadData\(["'](.+?)["']\)/g, (_, module) ->
                """require("#{ wiki2fs module }")"""

    ###
    This function transforms the content of a Lua source file
    into a wiki Scribunto module.

    @summary Transforms Lua sources into Scributo modules.

    @param {string} lua - The whole Lua source code.
    @return {string} The Scribunto source corresponding to `lua`.
    ###
    toModule: (lua) ->
        lua.replace /local mw = require\(['"]mw['"]\)\n+/g, ''
            .replace /require\("(.+?)"\)/g, (_, module) ->
                "mw.loadData('#{ fs2wiki module }')"
            .replace /require\('(.+?)'\)/g, (_, module) ->
                "require('#{ fs2wiki module }')"

    wikicode: (text) ->
        @colore @p text

for own name, filter of filterMacros
    @[name] = makeFilterMacro filter.bind filterMacros
