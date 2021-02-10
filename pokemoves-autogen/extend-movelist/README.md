Here I put anything needed to extend a movelist in a move page.

# Usage
## Build inverted data module
The lua script `invert-data.lua` build a lua source with data for moves of
a specified generation from `pokemoves-data.lua`. It's quite bad right now,
so it must be run from the parent of this directory (`pokemoves-autogen`).
The usage is as simple as
```bash
lua extend-movelist/invert-data.lua <gen>
```
where gen is the generation for which you want to build the inverted module.

## Run the bot script
In this repo's `bot` directory (path relative from here should be `../../bot`)
there's a script `updatemovelist.py`. This script does the job, but requires
a couple of things:
- you should of course copy it into your pwb's `scripts/userscripts`
- in that same directory you must symlink (or copy if you prefer) this
  directory as `movelistlib` with something like
  ```bash
ln -s /path/to/your/wiki-utils/pokemoves-autogen/extend-movelist movelistlib
  ```
- you should change the script to have your path to the `wiki-utils` directory
- you should build the inverted data module as explained in the previous
  section

All this done, you should be able to run
```bash
python pwb.py updatemovelist -cat:"Mosse"
```
and you're done.

NOTE: that's not true, right now the script does not update tutors. This is because tutors differ a lot from other kinds, and in SpSc they're very few, so I decided that update them by hand was more time efficient than handling them this script. Of course this could change in the future.

# TODO
- make tutor work
