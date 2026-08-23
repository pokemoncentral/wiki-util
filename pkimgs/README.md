Here are various utilities for [Pokémon images subpages](https://wiki.pokemoncentral.it/Categoria:Sottopagine_immagini_Pok%C3%A9mon).

## Configuration
Run `create_symlinks.sh` script in this directory to create symlinks of these files in Pywikibot directory (whic is imported from `config.sh` file in `bash` folder).

## Scripts
Each script has a documentation, here is a recap.

### pkimgs-data.py
This script downloads various data from wiki, main arguments are the following (for all optional arguments see code):
- `catlist` is used to retrieve all images contained in a category (recursively) and save them in a text file; value can be the name of a category or `all`, in this case all categories are updated. It takes some minutes, so it is advisable to do this only when needed. Files are saved in `<Pywikibot directory>/data/pokepages-catlists` as `<category name>.txt`, with colon replaced by semicolon.
- `pokelist` reads all category files and retrieves all images of a certain Pokémon, searching for its name or Pokédex number; do note that some of them won't be found because of their name containing something different from Pokémon names (for example images containing the name of a legendary duo or trio). Value can be a Dex number, a list of Dex numbers separated by comma, or `all`, in this case all Pokémon are evaluated. Files are saved in `<Pywikibot directory>/data/pokepages-pokelists` with name `<ndex>.txt`.
- `pokerank` counts how many images are available for each Pokémon: when the value is a Dex number counts images for that Pokémon, when it is `all` a ranking is created to see who has the highest number of images. Not useful actually, but funny :)
- `download` downloads wikicode of pages, value works as `pokelist` and pages are saved in `<Pywikibot directory>/data/pokepages-downloaded` with name `<ndex>.txt`. This can take some time if all subpages are retrieved.

Command needed to do everything:
```
python3 pwb.py pkimgs-data --catlist all --pokelist all --pokerank all --download all
```

### pkimgs-create.py
This script creates subpages from scratch, but do note that artworks section needs to be checked by hand because some of them don't follow standard name conventions: see category [Artwork Pokémon](https://wiki.pokemoncentral.it/Categoria:Artwork_Pok%C3%A9mon) for missing artworks. Only argument `pokepage` is needed (for all optional arguments see code) and its value works as `pokelist` in `pkimgs-data.py`. Command needed to create all subpages:
```
python3 pwb.py pkimgs-create --pokepage all
```

### pkimgs-update.py
This script updates subpages, each page is read from `<Pywikibot directory>/data/pokepages-downloaded`: missing files are automatically downloaded, but existing ones won't be automatically re-downloaded. Main arguments are the following (for all optional arguments see code):
- `updatepoke` specifies which Pokémon need to be updated, value works as `pokelist` in `pkimgs-data.py` but `all` updates all pages contained in `<Pywikibot directory>/data/pokepages-downloaded`, _not_ all Pokémon subpages; edited page is saved in `<Pywikibot directory>/data/pokepages-updated` with name `<ndex>.txt`, but only if the edited page is actually different from the original.
- `section` can be used to specify what section(s) to update, value can be `all` (default), `artwork`, `main`, `spinoff`.
- `upload` uploads updated pages to wiki, its value works as `updatepoke`. Do note that `<Pywikibot directory>/data/pokepages-updated` is not cleared automatically, so remember to do it when necessary.
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

### pkimgs-compare-wikis.py
This script compares categories in two wikis to check if some images from one may be missing from the other. Specifically, for each ndex the script counts the number of images in the two categories, if different they are all printed and a manual check is needed (no automatic check is performed because it would require a lot of effort to handle all naming conventions).

### sprelli.py
This script fills "Sprello" template fields: it can be used to mass upload images in a directory or to update an entire category on Pokémon Central Wiki.

### sprelli-redirects.py
This script creates needed redirects for game sprites/models whose name follows main games naming convention (an example is Pokémon HOME).

### pokeartwork.py
This script fills "Pokeartwork" template fields: it can be used to mass upload images in a directory or to update an entire category on Pokémon Central Wiki.

### pkimgs-sprite-template.py
This script updates Sprite template in Pokémon pages.

## Other files
### pokepages-exceptions
These files contain particular cases, with ad-hoc wikicode that will be read and imported directly.

### pokepages-utils
Each file contains one entry per line; files that list Pokémon (e.g. `femaleonly.txt`) contain their Pokédex numbers, not their names.
- `abbr-pairs.txt` maps Bulbapedia and PCWiki abbrs for alternative forms.
- `artsources.json` lists abbreviations of sources for artworks.
- `categories-names.json` contains data of some categories with Pokémon images, is used by `pkimgs-compare-wikis.py`.
- `cats.txt` contains all categories with Pokémon images (they are retrieved recursively).
- `goforms.txt` lists abbreviations of events exclusive to Pokémon GO.
- `redirect_ranger.txt` lists redirects for Pokémon Ranger sprites.
- `singleMS.txt` lists Pokémon that have the same mini sprite for base form and all alternative forms.

### extra.txt
This file lists images that exist only as redirect but are needed because automatic creation/update of pages leads to mistakes, for example:
- Mini sprites from generation I and II.
- Shiny models of Minior from Pokémon HOME.
