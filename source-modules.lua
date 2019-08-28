-- Add my modules' dir to lua's package.path to allow requiring them
package.path = table.concat{
    package.path,
    ";/home/Mio/Flavio/2-giochi/Pokémon/Wiki/Script/wiki-lua-modules/?.lua"
}
