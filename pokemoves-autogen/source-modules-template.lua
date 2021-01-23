-- This file's content should be consistent with config.sh

-- Add my modules' dir to lua's package.path to allow requiring them
package.path = "lua-scripts/?.lua;" ..
    package.path ..
    ";/path/to/lua/modules/?.lua"

-- Base dir for intermediate outputs
tempoutdir = "intermediate-outputs"
-- Base dir for pokemoves-data output
resultoutdir = "learnlist-gen"

-- Only require pokemoves if explicitly asked
pokemoves = {}

function run_when_imported(load)
    if load then
        -- Require the local pokemoves as a global variable named pokemoves
        pokemoves = require(resultoutdir .. ".pokemoves-data")
    end
end

return run_when_imported
