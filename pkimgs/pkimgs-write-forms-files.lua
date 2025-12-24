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
function addAbbrRow(forms, row)
    local abbr = row[1]
    local abbrSince = row[2]
    local abbrUntil = row[3]
    return forms .. abbr:gsub('base', '') .. ',' .. abbrSince .. ',' .. abbrUntil .. '\n'
end

-- write text to file, creating it if not existing ot overwriting it if existing
function writeFile(filePath, fileContent)
    local file = io.open(filePath, "w")
    file:write(fileContent)
    file:close()
end

--[[

Initial setup: require needed modules and extract some data that will be used later

--]]

-- retrieve full path of this script
local scriptPath = debug.getinfo(1, "S").source:sub(2)
scriptPath = io.popen("realpath '" .. scriptPath .. "'", 'r'):read('a')
scriptPath = scriptPath:gsub('[\n\r]*$', '')
-- get script directory and find forms files directory
local scriptDir = getDirName(scriptPath)
local formsDir = scriptDir .. '/pokepages-pokeforms'
-- add to package.path directory with config.lua
addToPath(getDirName(scriptDir) .. '/lua')
-- add to package.path directory with other modules
local config = require('config')
addToPath(config.modulesPath)

-- require needed modules
local af = require('AltForms-data')
local uf = require('UselessForms-data')
local bf = require('BothForms-data')
local pd = require('Poké-data')
-- extract some data that will be used later
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
local numbers = { 1, 3, 6, 25, 26, 83, 181, 428, 585, 658, 670 }
for n = 1, 1500 do numbers[n] = n end
for _,n in pairs(numbers) do
    local ndex = string.format('%04d', n)
    local gamesOrder = nil
    -- BothForms contains final order for Pokémon with entries in both AltForms and UselessForms
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
            -- abbr, since, until
            -- done this way because forms that were removed from game code and
            -- then added back in later games need to be splitted in multiple rows
            local formsRows = { { abbr, '', '' } }
            if (bf[n] ~= nil) then
                formsRows[1][2] = bf[n].since[abbr]
                if (bf[n]['until'] ~= nil) then
                    formsRows[1][3] = bf[n]['until'][abbr] or ''
                end
            elseif (af[n] ~= nil) then
                formsRows[1][2] = af[n].since[abbr]
                if (af[n]['until'] ~= nil) then
                    formsRows[1][3] = af[n]['until'][abbr] or ''
                end
            elseif (uf[n] ~= nil) then
                formsRows[1][2] = uf[n].since[abbr]
                if (uf[n]['until'] ~= nil) then
                    formsRows[1][3] = uf[n]['until'][abbr] or ''
                end
            end
            -- Gigamax only exists in spsc
            if (abbr == 'Gi' and contains(af.formgroups.gigamax, name:lower())) then
                formsRows[1][3] = 'spsc'
            end
            -- Megaevolution doesn't exist between spsc and sv (included)
            if (contains({ 'M', 'MX', 'MY' }, abbr) and contains(megas, name:lower()) and contains({ 'xy', 'roza' }, formsRows[1][2])) then
                formsRows[2] = { abbr, 'lpza', formsRows[1][3] }
                formsRows[1] = { abbr, formsRows[1][2], 'usul' }
                if (n < 151) then
                    formsRows[1][3] = 'lgpe'
                else
                    formsRows[1][3] = 'usul'
                end
            end
            -- regional forms don't exist in dlps, lpa, lpza
            if (abbr == 'A' and contains(af.formgroups.alola, name:lower())) then
                formsRows[1] = { abbr, 'sl', 'spsc' }
                formsRows[2] = { abbr, 'sv', 'sv' }
            end
            if (abbr == 'G' and contains(af.formgroups.galar, name:lower())) then
                formsRows[1] = { abbr, 'spsc', 'spsc' }
                formsRows[2] = { abbr, 'sv', 'sv' }
            end
            -- Tauros has different abbrs but does not exist in LPZA, so I'll ignore it
            if (abbr == 'P' and contains(af.formgroups.paldea, name:lower())) then
                formsRows[1] = { abbr, 'sv', 'sv' }
            end
            -- Pikachu with hat don't exist in dlps, lpa, lpza
            if (n == 25 and contains({ 'O', 'H', 'Si', 'U', 'K', 'A', 'Co' }, abbr)) then
                formsRows[1] = { abbr, formsRows[1][2], 'spsc' }
                formsRows[2] = { abbr, 'sv', 'sv' }
            end
            -- finally add row(s)
            for _,row in pairs(formsRows) do
                forms = addAbbrRow(forms, row)
            end
        end
        -- enable the following line and disable last one if testing
        -- print(forms)
        writeFile(pokePath, forms)
    end
end
