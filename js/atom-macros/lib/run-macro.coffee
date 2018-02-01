###
@fileoverview

Created by Davide on 1/30/18.
###

require 'coffeescript/register'
fs = require 'fs'
util = require 'util'
macros = require './macros'


TEST = process.env.NODE_ENV == 'testing'


applyMacro = (text, macroName) ->
    global.getActiveTextEditor = () ->
        getText: () -> text
        setText: (text) -> text

    macros[macroName]()


macrosOnFile = (file, macroNames...) ->
    contents = await util.promisify(fs.readFile) file, 'utf-8'
    processedContents = macroNames.reduce applyMacro, contents
    await util.promisify(fs.writeFile) file, processedContents


module.exports = if TEST \
    then {applyMacro, macrosOnFile} \
    else macrosOnFile
