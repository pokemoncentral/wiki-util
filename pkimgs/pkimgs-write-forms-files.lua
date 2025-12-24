--[[

This script is used to automatically generate all files with forms data in
pokepages-pokeforms, that are used by other scripts in this directory. Each file
is named as <ndex>.txt and each row should contain form abbreviation, game where
it first appeared and, if applicable, game where it last appeared.

--]]

-- print a list/table, used during development/debug
function dump(o)
    if type(o) == 'table' then
        local s = '{ '
        for k,v in pairs(o) do
            if type(k) ~= 'number' then k = '"' .. k .. '"' end
            s = s .. '[' .. k .. '] = ' .. dump(v) .. ', '
        end
        return s .. '} '
    else
        return tostring(o)
    end
end

-- add a directory to package.path
function addToPath(newPath)
    package.path = package.path .. ';' .. newPath .. '/?.lua'
end

-- get path of directory contaning item (without trailing slash)
function getDirName(path)
    local dirname, filename = path:match('^(.*)/([^/]-)$')
    dirname = dirname or ''
    filename = filename or scriptPath
    return dirname
end

-- check if list contains item
function contains(list, item)
    local found = false
    for i,l in pairs(list) do
        if (l == item) then
            found = true
            break
        end
    end
    return found
end

-- add a row to text file with forms
function addAbbrRow(forms, abbr, abbrSince, abbrUntil)
    return forms .. abbr:gsub('base', '') .. ',' .. abbrSince .. ',' .. abbrUntil .. '\n'
end

-- write text to file, creating it if not existing ot overwriting it if existing
function writeFile(filePath, fileContent)
    local file = io.open(filePath, "w")
    file:write(fileContent)
    file:close()
end

-- retrieve full path of this script
local scriptPath = debug.getinfo(1, "S").source:sub(2)
scriptPath = io.popen("realpath '" .. scriptPath .. "'", 'r'):read('a')
scriptPath = scriptPath:gsub('[\n\r]*$', '')
-- get script directory and find forms files directory
scriptDir = getDirName(scriptPath)
formsDir = scriptDir .. '/pokepages-pokeforms'
-- add to package.path directory with config.lua
addToPath(getDirName(scriptDir) .. '/lua')
-- add to package.path directory with other modules
local config = require('config')
addToPath(config.modulesPath)
-- print(package.path)

-- require needed modules
local af = require('AltForms-data')
local uf = require('UselessForms-data')
local bf = require('BothForms-data')
local pd = require('Poké-data')
-- extract some data that will be used later
local gigas = af.formgroups.gigamax
local megasSingle = af.formgroups.mega
local megasMultiple = af.formgroups.megaxy
local megas = {}
table.move(megasSingle, 1, #megasSingle, 1, megas)
table.move(megasMultiple, 1, #megasMultiple, #megas + 1, megas)

--[[

Process all Pokémon; numbers without an entry in *Forms/data are skipped, so
the upper limit can be any value greater than last Pokémon's Pokédex number.

--]]

-- The following line is needed, otherwise next one fails because numbers is null
numbers = { 1, 3, 6, 25, 26, 83, 181, 428, 585, 658, 670 }
for n = 1, 1500 do numbers[n] = n end
for _,n in pairs(numbers) do
    local ndex = string.format('%04d', n)
    local gamesOrder = nil
    if (bf[n] ~= nil) then
        gamesOrder = bf[n].gamesOrder
    elseif (af[n] ~= nil) then
        gamesOrder = af[n].gamesOrder
    elseif (uf[n] ~= nil) then
        gamesOrder = uf[n].gamesOrder
    end
    if (gamesOrder == nil) then
        -- print('------ Skipping ' .. n) -- [debug]
    else
        local name = pd[n].name
        local forms = ''
        local pokePath = formsDir .. '/' .. ndex .. '.csv'
        print('------ Processing ' .. pokePath .. ' ' .. name)
        -- print(dump(gamesOrder)) -- [debug]
        for _,abbr in pairs(gamesOrder) do
            local abbrSince = ''
            local abbrUntil = ''
            if (bf[n] ~= nil) then
                abbrSince = bf[n].since[abbr]
                if (bf[n]['until'] ~= nil) then
                    abbrUntil = bf[n]['until'][abbr] or ''
                end
            elseif (af[n] ~= nil) then
                abbrSince = af[n].since[abbr]
                if (af[n]['until'] ~= nil) then
                    abbrUntil = af[n]['until'][abbr] or ''
                end
            elseif (uf[n] ~= nil) then
                abbrSince = uf[n].since[abbr]
                if (uf[n]['until'] ~= nil) then
                    abbrUntil = uf[n]['until'][abbr] or ''
                end
            end
            -- Gigamax only exists in spsc
            if (abbr == 'Gi' and contains(gigas, name:lower())) then
                abbrUntil = 'spsc'
            end
            -- Megaevolution doesn't exist between spsc and sv (included)
            if (contains({ 'M', 'MX', 'MY' }, abbr) and contains(megas, name:lower()) and contains({ 'xy', 'roza' }, abbrSince)) then
                forms = addAbbrRow(forms, abbr, abbrSince, 'lgpe')
                forms = addAbbrRow(forms, abbr, 'lpza', abbrUntil)
            else
                forms = addAbbrRow(forms, abbr, abbrSince, abbrUntil)
            end
        end
        -- enable the following line and disable last one if testing
        print(forms)
        -- writeToFile(pokePath, forms)
    end
end
