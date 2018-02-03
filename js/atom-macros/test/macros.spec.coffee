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
    first line<br>second line
'''
goodHTML = '''
    <span class="text-small">small text</span>
    <span class="text-big">big text</span>
    first line<div>second line</div>
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


basicBehavior = (source, expected, macroName) ->
    () ->
        result = runMacros.applyMacro source, macroName
        result.should.equal expected


idempotence = (source, macroName) ->
    () ->
        once = runMacros.applyMacro source, macroName
        twice = runMacros.applyMacro once, macroName
        once.should.equal twice


describe 'big', () ->

    # TODO: better use of match
    it 'should turn big tags to span class="text-big"', () ->
        result = runMacros.applyMacro badHTML, 'big'
        goodBig = goodHTML.match(/<span class="text-big">.+<\/span>/)[0]
        result.should.contain goodBig

    it 'should be idempotent', \
        idempotence badHTML, 'big'


describe 'br', () ->

    # TODO: better use of match
    it 'should turn br tags to div', () ->
        result = runMacros.applyMacro badHTML, 'br'
        goodBr = goodHTML.match(/.*<div>.+<\/div>.*/)[0]
        result.should.contain goodBr

    it 'should be idempotent', \
        idempotence badHTML, 'br'


describe 'colore', () ->

    # TODO: better use of match
    it 'should turn colore template to colore modules', () ->
        result = runMacros.applyMacro badWikicode, 'colore'
        goodColore = goodWikicode.match(/\{\{#invoke: colore \| .+\}\}/)[0]
        result.should.contain goodColore

    it 'should be idempotent', \
        idempotence badWikicode, 'colore'


describe 'p', () ->

    # TODO: better use of match
    it 'should turn p template to plain links', () ->
        result = runMacros.applyMacro badWikicode, 'p'
        goodP = goodWikicode.match(/\[\[.+\]\]/)[0]
        result.should.contain goodP

    it 'should be idempotent', \
        idempotence badWikicode, 'p'


describe 'small', () ->

    # TODO: better use of match
    it 'should turn small tags to span class="text-small"', () ->
        result = runMacros.applyMacro badHTML, 'small'
        goodSmall = goodHTML.match(/<span class="text-small">.+<\/span>/)[0]
        result.should.contain goodSmall

    it 'should be idempotent', \
        idempotence badHTML, 'small'


describe 'tags', () ->

    it 'should turn all tags to a better version', \
        basicBehavior badHTML, goodHTML, 'tags'

    it 'should be idempotent', \
        idempotence badHTML, 'tags'


describe 'toLua', () ->

    it 'should change module names and remove mw.loadData', \
        basicBehavior luaModule, luaSource, 'toLua'

    it 'should be idempotent', \
        idempotence luaModule, 'toLua'


describe 'toModule', () ->

    it 'should prepend Module and insert mw.loadData for double quotes', \
        basicBehavior luaSource, luaModule, 'toModule'

    it 'should be idempotent', \
        idempotence luaSource, 'toModule'


describe 'wikicode', () ->

    it 'should turn the wikicode to a better version', \
        basicBehavior badWikicode, goodWikicode, 'wikicode'

    it 'should be idempotent', \
        idempotence badWikicode, 'wikicode'
