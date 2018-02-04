###
@fileoverview

Created by Davide on 1/30/18.
###

require 'coffeescript/register'
fs = require 'fs'
util = require 'util'
macros = require './macros'
path = require 'path'


TEST = process.env.NODE_ENV == 'testing'

applyMacro = (text, macroName, fileName) ->
    global.getActiveTextEditor = () ->
        getText: () -> text
        setText: (text) -> text
        getTitle: () -> path.basename fileName

    macros[macroName]()


macrosOnFile = (file, macroNames...) ->
    contents = await util.promisify(fs.readFile) file, 'utf-8'
    processedContents = macroNames.reduce ((text, macroName) -> applyMacro text, macroName, file), contents
    await util.promisify(fs.writeFile) file, processedContents


module.exports = if TEST \
    then {applyMacro, macrosOnFile} \
    else macrosOnFile
