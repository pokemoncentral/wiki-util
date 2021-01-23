# Configuration file template. Create your config file with the name
# "config.sh" in this directory

# Path to repository pokemoncentral/wiki-lua-modules
export MODULESPATH="/path/to/lua/modules/"

# Local port to which bind the container's database. Any non used port will be fine
export CONTAINERPORT=43861

# Default name for the container, used for ./do-things.sh -D
export CONTAINERDEFAULTNAME="moves-db"

# Whether the resultin pokemoves-data should be splitted or not. Any
# value different from "no" splits
export SPLIT="no"

# ================================== Constants ==============================
# These are just constants shared between scripts. There's no need to change
# them on your config

# Base name of the result module
export MODULENAME="PokéMoves-data"

# Base name for temporary results
export TMPMODULENAME="pokemoves-data"

# List of Pokémon names
export POKELIST="lists/pokemon-names.list"

# Base dir for intermediate outputs
export TEMPOUTDIR="intermediate-outputs"

# Lua scripts dir
export LUASCRPITSDIR="lua-scripts"

# Output dir
export OUTPUTMODULEDIR="learnlist-gen"
