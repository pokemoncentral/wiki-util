/**
 * @fileoverview
 *
 * Created by Davide on 1/30/18.
 */

require('coffeescript/register');

const argv = require('yargs')
    .array('macros')
    .argv;

const runMacro = require('./lib/run-macro');

const FILE = argv.file || argv._[0];
const MACROS = argv.macros
    || argv.macro && [argv.macros]
    || argv._.slice(1);

runMacro(FILE, ...MACROS).done();
