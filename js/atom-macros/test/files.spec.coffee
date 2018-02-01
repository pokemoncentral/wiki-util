###
@fileoverview

Created by Davide on 2/1/18.
###

require 'coffeescript/register'
fs = require 'fs'
util = require 'util'
should = require 'chai'
    .should()
runMacros = require '../lib/run-macro'
stat = util.promisify fs.stat
readFile = util.promisify fs.readFile


describe 'run-macros', () ->
    before () ->
        @fileName = "#{ __dirname }/lua/test.lua"
        @modTime = () ->
            (await stat @fileName).mtimeMs
        @readFile = () ->
            await readFile @fileName, 'utf-8'

    it 'should modify the file in place', () ->
        oldModTime = await @modTime()
        await runMacros.macrosOnFile @fileName, 'toModule'
        newModTime = await @modTime()

        oldModTime.should.be.below newModTime

    it 'should modify the file accordingly to the macro', () ->
        macroName = 'toLua'

        oldFileContents = await @readFile()
        result = runMacros.applyMacro oldFileContents, macroName

        await runMacros.macrosOnFile @fileName, macroName
        newFileContents = await @readFile()

        newFileContents.should.equal result
