Here are various utilities for [Pokémon images subpages](https://wiki.pokemoncentral.it/Categoria:Sottopagine_immagini_Pok%C3%A9mon).

## Configuration
To copy all these files in Pywikibot directory, run
```
bash copy.sh botdir
```
To copy here files from Pywikibot directory, run
```
bash copy.sh here
```
Pywikibot directory is imported from `config.sh` file in `bash` folder.

## Scripts
### pkimgs-data.py
This script downloads various data from wiki, main arguments are the following (for all optional arguments see code):
- `catlist` is used to retrieve all images contained in a category and save them in a text file; value can be the name of a category or `all`, in this case all categories are updated. By default `all` doesn't actually update all categories: in fact most of them are related to old games that won't receive updates, therefore it is not necessary to check for new images. To force the download of all categories (for example when retrieving them for the first time), argument `--catsfile data/utils/allcats.txt` can be added to command. Do note that retrieving images takes some time and updating all categories will take several minutes, so it is advisable to do this only when needed. Files are saved in `<bot directory>/data/catlists` as `<category name>.txt`, with colon replaced by semicolon.
- `pokelist` reads all category files and retrieves all images of a certain Pokémon, searching for its name or Pokédex number; do note that some of them won't be found because of their name containing something different from Pokémon names (for example images containing the name of a legendary duo or trio). Value can be a Dex number, a list of Dex numbers separated by comma, or `all`, in this case all Pokémon are evaluated. Files are saved in `<bot directory>/data/pokelists` with name `<ndex>.txt`.
- `pokerank` counts how many images are available for each Pokémon: when the value is a Dex number counts images for that Pokémon, when it is `all` a ranking is created to see who has the highest number of images. Not useful actually, but funny :) (this is also the only thing to be printed)
- `download` downloads wikicode of pages, value works as `pokelist` and pages are saved in `<bot directory>/data/pokepages-downloaded` with name `<ndex>.txt`. This can take some time if all subpages are retrieved.

Command needed to retrieve categories and create/update pokelists:
```
python3 pwb.py pkimgs-data --catlist all --pokelist all
```
Command needed to download all current subpages:
```
python3 pwb.py pkimgs-data --download all
```

### pkimgs-create.py
This script creates subpages from scratch, but do note that artworks section needs to be checked by hand because some of them don't follow standard name conventions: see category [Artwork Pokémon](https://wiki.pokemoncentral.it/Categoria:Artwork_Pok%C3%A9mon) for missing artworks. Only argument `pokepage` is needed (for all optional arguments see code) and its value works as `pokelist` in `pkimgs-data.py`. Command needed to create all subpages:
```
python3 pwb.py pkimgs-create --pokepage all
```

### pkimgs-update.py
This script updates subpages, each page is read from `<bot directory>/data/pokepages-downloaded`: missing files are automatically downloaded, but existing ones won't be automatically re-downloaded. Main arguments are the following (for all optional arguments see code):
- `updatepoke` specifies which Pokémon need to be updated, value works as `pokelist` in `pkimgs-data.py` but `all` updates all pages contained in `<bot directory>/data/pokepages-downloaded`, _not_ all Pokémon subpages; edited page is saved in `<bot directory>/data/pokepages-updated` with name `<ndex>.txt`, but only if the edited page is actually different from the original.
- `section` can be used to specify what section(s) to update, value can be `all` (default), `artwork`, `main`, `spinoff`.
- `upload` uploads updated pages to wiki, its value works as `updatepoke`. Do note that `<bot directory>/data/pokepages-updated` is not cleared automatically, so remember to do it when necessary.
- `summary` allows to change default edit summary when uploading pages to wiki.

Command needed to fully update all subpages and save them in local files:
```
python3 pwb.py pkimgs-update --updatepoke all
```

Command needed to upload all updated subpages:
```
python3 pwb.py pkimgs-update --upload all
```

### pkimgstools.py
This file contains functions that are used by previous scripts, it is not intended to be launched directly.

## Other files
### utils
Each file contains one entry per line; files that list Pokémon (e.g. `femaleonly.txt`) contain their Pokédex numbers, not their names.
- `allcats.txt` contains a list of all relevant categories (artworks, main series sprites/models, spin-offs sprites/models).
- `artsources.txt` lists abbreviations of sources for artworks.
- `cats.txt` is a sublist of `allcats.txt` that excludes old games that won't receive updates and only contains categories that are likely to change.
- `femaleonly.txt` lists female-only Pokémon.
- `genderdiffs.txt` lists Pokémon with gender differences, included those that are treated as useless forms.
- `genderforms.txt` lists gender differences that are treated as alternative forms.
- `goforms.txt` lists abbreviations of events exclusive to Pokémon GO.
- `pokes_de.txt` maps German names to Italian/English names (used for interwikis).
- `pokes_fr.txt` same but for French names.
- `pokes_ndex.txt` maps ndexes to names.
- `redirect_ranger.txt` lists redirects for Pokémon Ranger sprites.
- `singleMS.txt` lists Pokémon that have the same mini sprite for base form and all alternative forms.
- `spsc.txt` lists Pokémon that exist in Pokémon Sword and Shield.

### pokeforms
Each Pokémon with one or more alternative forms has a file named `<ndex>.txt` in `<bot directory>/data/pokeforms`; each line contains abbreviations of form (or empty string for base form), first game where it exists and last game where it exists (the latter if empty will automatically be interpreted as last game available), separated by comma. If a Pokemon does not exist in Sword and Shield it is not necessary to specify `usul`/`lgpe` for his base form, because `spsc.txt` is used instead to evaluate it.

### exceptions
These files contain particular cases, with ad-hoc wikicode that will be read and imported directly.

### extra.txt
This file lists images that exist only as redirect but are needed because automatic creation/update of pages leads to mistakes, specifically:
- Mini sprites from generation I and II.
- Shiny models of Minior from Pokémon HOME.
