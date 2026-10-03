import json
import os
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar, Self

import typer
from typer import Option

from pokeapi_moves.lib import sh
from pokeapi_moves.pokeapi_db import generated_file_name

cli = typer.Typer()

forms_sql_output = generated_file_name("forms.sql")


@cli.command()
def forms(
    alt_forms_lua: Annotated[str, Option(help="The path to AltForms-data.lua")],
    output: Annotated[
        str,
        Option(help="The generated SQL output path. Mostly useful for testing"),
    ] = forms_sql_output,
):

    lua_export = sh(
        "lua", "-", input=LuaFormExport.lua_script(alt_forms_lua), pipe_stdio=False
    ).stdout
    alt_forms_json: list[LuaFormExport] = json.loads(
        lua_export, object_hook=LuaFormExport.from_json
    )
    alt_forms_sql_values = ",\n".join(f.as_sql_row() for f in alt_forms_json)
    with open(output, "w", encoding="utf-8") as forms_sql:
        forms_sql.write(f"""
create table lua_forms_export (
    id integer primary key,
    name text,
    abbr text,
    ndex int
);
insert into lua_forms_export
(name, abbr, ndex)
values
{alt_forms_sql_values};

drop table if exists pkmn_form;
create table if not exists pkmn_form (
    id integer primary key,
    form_id int,
    pkmn_id int,
    ndex int,
    name text,
    abbr text,
    form_order int
);
insert into pkmn_form(form_id, pkmn_id, ndex, name, abbr, form_order)
select
    f.id,
    p.id,
    l.ndex,
    fn.name,
    l.abbr,
    f."order"
from pokemon_v2_pokemonform f
    join pokemon_v2_pokemon p on p.id = f.pokemon_id
    join pokemon_v2_pokemonformname fn on fn.pokemon_form_id = f.id
    join lua_forms_export l on fn.name = l.name
        and l.ndex = p.pokemon_species_id
where
    not exists (select 1 from pkmn_form)
    and fn.language_id = (
        select id
        from pokemon_v2_language
        where iso3166 = 'it'
        limit 1
    )
    and p.pokemon_species_id in (
        select pokemon_species_id
        from pokemon_v2_pokemon
        group by pokemon_species_id
        having count(*) > 1
    )
""".strip())


# Short name for readability in string interpolation
def s(s: str) -> str:
    """Create SQL string literals"""
    return "'%s'" % s.replace("'", "''")


def require_lua(target_var: str, file: str) -> str:
    parent, file_name = os.path.split(file)
    extensionless, _ = os.path.splitext(file_name)
    return f"""
        package.path = '{parent}/?.lua;' .. package.path
        local {target_var} = require('{extensionless}')
    """


@dataclass(kw_only=True)
class LuaFormExport:
    abbr: str
    name: str
    ndex: int

    lua_var: ClassVar[str] = "altForms"

    def as_sql_row(self) -> str:
        return f"({s(self.name)}, {s(self.abbr)}, {self.ndex})"

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> Self:
        return cls(**json_dict)

    @classmethod
    def lua_script(cls, alt_forms_lua: str) -> str:
        return f"""
            {require_lua(cls.lua_var, alt_forms_lua)}
            local json = require('cjson')

            local res = {{}}
            for key, data in pairs({cls.lua_var}) do
                if type(key) ~= 'number' and data.names then
                    local ndex
                    for ndex_key, ndex_data in pairs({cls.lua_var}) do
                        -- Intentionally matching on table address equality
                        if ndex_data == data and type(ndex_key) == 'number' then
                            ndex = ndex_key
                        end
                    end
                    for abbr, name in pairs(data.names) do
                        table.insert(res, {{
                            abbr = abbr,
                            name = name,
                            ndex = ndex
                        }})
                    end
                end
            end

            print(json.encode(res))
        """
