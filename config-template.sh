# Configuration file template. Create your config file with the name
# "config.sh" in this directory

# Path to repository pokemoncentral/wiki-lua-modules
export MODULESPATH="/path/to/lua/modules/"

# Local port to which bind the container's database. Any non used port will be fine
export CONTAINERPORT=43861

# Default name for the container, used for ./do-things.sh -D
export CONTAINERDEFAULTNAME="moves-db"
