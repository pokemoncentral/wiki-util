###
@fileoverview

Created by Davide on 1/31/18.
###

require 'coffeescript/register'
should = require 'chai'
    .should()
runMacros = require '../lib/run-macro'


luaModule = '''
    local ms = require('Modulo:MiniSprite')
    local txt = require('Modulo:Wikilib/strings')
    local c = mw.loadData('Modulo:Colore/data')
'''
luaSource = '''
    local ms = require('MiniSprite')
    local txt = require('Wikilib-strings')
    local c = require("Colore-data")
'''


describe 'toLua', () ->

    it 'should change module names and remove mw.loadData', () ->
        result = runMacros.applyMacro luaModule, 'toLua'
        result.should.equal luaSource

    it 'should be idempotent', () ->
        once = runMacros.applyMacro luaModule, 'toLua'
        twice = runMacros.applyMacro once, 'toLua'
        once.should.equal twice


describe 'toModule', () ->

    it 'should prepend Module and insert mw.loadData for double quotes', () ->
        result = runMacros.applyMacro luaSource, 'toModule'
        result.should.equal luaModule

    it 'should be idempotent', () ->
        once = runMacros.applyMacro luaSource, 'toModule'
        twice = runMacros.applyMacro once, 'toModule'
        once.should.equal twice
