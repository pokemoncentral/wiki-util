###
@fileoverview

Created by Davide on 1/31/18.
###

require 'coffeescript/register'
should = require 'chai'
    .should()
runMacros = require '../lib/run-macro'

badHTML = '''
    <small>small text</small>
    <big>big text</big>
'''
goodHTML = '''
    <span class="text-small">small text</span>
    <span class="text-big">big text</span>
'''
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
badWikicode = '''
    {{colore pcwiki dark}}
    {{p|Luxio}}
'''
goodWikicode = '''
    {{#invoke: colore | pcwiki | dark}}
    [[Luxio]]
'''


describe 'big', () ->

    # TODO: better use of match
    it 'should turn big tags into span class="text-big"', () ->
        result = runMacros.applyMacro badHTML, 'big'
        goodBig = goodHTML.match(/<span class="text-big">.+<\/span>/)[0]
        result.should.contain goodBig

    it 'should be idempotent', () ->
        once = runMacros.applyMacro badHTML, 'big'
        twice = runMacros.applyMacro once, 'big'
        once.should.equal twice


describe 'colore', () ->

    # TODO: better use of match
    it 'should turn colore template in colore modules', () ->
        result = runMacros.applyMacro badWikicode, 'colore'
        goodColore = goodWikicode.match(/\{\{#invoke: colore \| .+\}\}/)[0]
        result.should.contain goodColore

    it 'should be idempotent', () ->
        once = runMacros.applyMacro badWikicode, 'colore'
        twice = runMacros.applyMacro once, 'colore'
        once.should.equal twice


describe 'small', () ->

    # TODO: better use of match
    it 'should turn small tags into span class="text-small"', () ->
        result = runMacros.applyMacro badHTML, 'small'
        goodSmall = goodHTML.match(/<span class="text-small">.+<\/span>/)[0]
        result.should.contain goodSmall

    it 'should be idempotent', () ->
        once = runMacros.applyMacro badHTML, 'small'
        twice = runMacros.applyMacro once, 'small'
        once.should.equal twice


describe 'tags', () ->

    it 'should turn all tags to a better version', () ->
        result = runMacros.applyMacro badHTML, 'tags'
        result.should.contain goodHTML

    it 'should be idempotent', () ->
        once = runMacros.applyMacro badHTML, 'tags'
        twice = runMacros.applyMacro once, 'tags'
        once.should.equal twice


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


describe.skip 'wikicode', () ->

    it 'should turn the wikicode to a better version', () ->
        result = runMacros.applyMacro badWikicode, 'wikicode'
        result.should.contain goodWikicode

    it 'should be idempotent', () ->
        once = runMacros.applyMacro badWikicode, 'wikicode'
        twice = runMacros.applyMacro once, 'wikicode'
        once.should.equal twice
