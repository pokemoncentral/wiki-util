# PokéAPI moves

Long story short, we generate Movelist and Learnlist for Pokémon Central wiki
from [PokéAPI](https://github.com/pokeapi/pokeapi).

## Usage

```bash
uv run pokeapi-moves movelist --move barrage --game gold-silver --learning-method level-up --wipe-db
uv run pokeapi-moves learnlist --tbd --wipe-db
# You get the point, list all options with
uv run pokeapi-moves --help
```

## Overall machinery

1. Create the sqlite PokéAPI database locally
2. Run some custom queries to gather data for Movelist or Learnlist
3. Spit out the Wikicode

### More details

1. PokéAPI is included as a submodule. We benefit a lot from direct access to
   the underlying database, more so than the REST API.
