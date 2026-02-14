Data used by various tools in this repository (`pkimgs`, `gccp`, ...). For data files, each Pokémon is identified by its National Pokédex number (without leading zeros) followed by form abbreviation if not base form, unless stated otherwise.
* `forms-availability.json`: games where each alternative form is available.
* `gender-data.json`: list of Pokémon that are always female, that have gander differences and that have gender differences that are treated as alternative forms. First and third list contain National Pokédex numbers without abbreviation, because are referred to the entire species; gender differences contain form abbreviation if they are referred to an alternative form.
* `poke-availability.json`: list of available Pokémon in each game from Generation 8 onwards (for previous generations can be easily generated using Pokédex number). If base form is available only Pokédex Number is included; if base form is not available but some alternative forms are, they are listed separately (see LPA for an example).
* `poke-names.json`: for each Pokémon contains its National Pokédex number and its names in all languages.
* `utils.py`: various utilities for Python scripts.
