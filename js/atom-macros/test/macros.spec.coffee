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
luaDict = '''
    {{-start-}}
    \'''Modulo:Test\'''
    local ms = require('Modulo:MiniSprite')
    local txt = require('Modulo:Wikilib/strings')
    local c = mw.loadData('Modulo:Colore/data')
    {{-stop-}}
'''
badWikicode = '''
    {{colore pcwiki}}
    {{colore pcwiki dark}}
    {{p|Luxio}}
    {{template call}}
'''
goodWikicode = '''
    {{#invoke: colore | pcwiki}}
    {{#invoke: colore | pcwiki | dark}}
    [[Luxio]]
    {{template call}}
'''


basicBehavior = (source, expected, macroName) ->
    () ->
        result = runMacros.applyMacro source, macroName
        result.should.equal expected


basicBehaviorMatch = (source, expected, macroName, pattern) ->
    () ->
        matches = expected.match new RegExp pattern, 'g'
        result = runMacros.applyMacro source, macroName
        matches.every (match) -> result.should.contain match


basicBehaviorFilename = (source, expected, macroName, filename) ->
    () ->
        result = runMacros.applyMacro source, macroName, filename
        result.should.equal expected


idempotence = (source, macroName, filename) ->
    () ->
        once = runMacros.applyMacro source, macroName, filename
        twice = runMacros.applyMacro once, macroName, filename
        once.should.equal twice


describe 'big', () ->

    it 'should turn big tags to span class="text-big"', \
        basicBehaviorMatch badHTML, goodHTML, 'big', \
            '<span class="text-big">.+</span>'

    it 'should be idempotent', \
        idempotence badHTML, 'big'


describe 'br', () ->

    it 'should turn br tags to div', \
        basicBehaviorMatch badHTML, goodHTML, 'br', '.*<div>.+</div>'

    it 'should be idempotent', \
        idempotence badHTML, 'br'


describe 'colore', () ->

    it 'should turn colore template to colore modules', \
        basicBehaviorMatch badWikicode, goodWikicode, 'colore', \
            /\{\{#invoke: colore \| .+\}\}/

    it 'should be idempotent', \
        idempotence badWikicode, 'colore'


describe 'p', () ->

    it 'should turn p template to plain links', \
        basicBehaviorMatch badWikicode, goodWikicode, 'p', /\[\[.+\]\]/

    it 'should be idempotent', \
        idempotence badWikicode, 'p'


describe 'small', () ->

    it 'should turn small tags to span class="text-small"', \
        basicBehaviorMatch badHTML, goodHTML, 'small', \
            '<span class="text-small">.+</span>'

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

describe 'moduleToDict', () ->

    it 'should turn the scributo to an uploadable dict', \
        basicBehaviorFilename luaModule, luaDict, 'moduleToDict', 'Test.lua'

    it 'should be idempotent', \
        idempotence luaModule, 'moduleToDict', 'Test.lua'
