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
delay = util.promisify setTimeout

describe 'run-macros', () ->
    before () ->
        @modTime = (fileName) ->
            (await stat fileName).mtimeMs

    it 'should modify the file in place', () ->
        fileName = "#{ __dirname }/lua/test.lua"

        oldModTime = await @modTime fileName
        await runMacros.macrosOnFile fileName, 'toModule'
        newModTime = await @modTime fileName

        oldModTime.should.be.below newModTime
