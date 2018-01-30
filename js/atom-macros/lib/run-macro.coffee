###
@fileoverview

Created by Davide on 1/30/18.
###

require 'coffeescript/register'

fs = require 'fs'
q = require 'q'

macros = require './macros'

module.exports = (file, macroNames...) ->
    q.nfcall fs.readFile, file, 'utf-8'

    .then (contents) ->
        applyMacro = (text, macroName) ->
            global.getActiveTextEditor = () ->
                getText: () -> text
                setText: (text) -> text

            macros[macroName]()

        macroNames.reduce applyMacro, contents

    .then (text) ->
        q.nfcall fs.writeFile, file, text
