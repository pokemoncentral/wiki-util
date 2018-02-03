# Atom-macros
This module is meant to be a standalone runner for macros defined for the 
[atom-macros](https://atom.io/packages/atom-macros) package of Atom text 
editor.

## Core concepts
The _atom-macros_ package leverages on a coffeescript file named
_macros.coffee_ in the Atom home directory. The central idea behind this module
is to replace such file with a link to a file under this module control, so
that the very same macros can be run both from  Atom and from the command 
line: in the former case, the editor content is mutated, in the latter the
specified files.

## Usage

### Atom usage
In order to be able to run the macros from within Atom, the _atom-macros_ 
package need to be installed, and the file containing the macros needs to be 
linked from the right path. This can be achieved with the following commands 
from the same directory containing this `README.md` file; prefix them with 
`export ATOM_HOME=[path]` to change the default value.

```bash
apm install atom-macros
apm ls | grep 'Community Packages' | awk '{print $NF}' | xargs dirname \
    | xargs -i ln -sf "$PWD/lib/macros.coffee" "{}/macros.coffee"
```

### Standalone usage
The standalone version is powered by node.js. Even though it's primarily 
written in Coffeescript, no compilation is required, thanks to the trick
of writing the entry point in plain JavaScript and importing Coffeescript 
files directly from within it. The node version is specified in the `.nvmrc` 
file, for the joy of nvm users. The module can be run like this, from within
the same directory containing this `README.md` file.

```bash
node run-macros.js [input_file] [macro_name...]
```

## Development

Testing is dome with the standard `mocha` setup, the only exception being the
use of Coffeescript for the test suites; tests can be run with `npm run test`.
