import json
import os
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar, Self

import typer
from typer import Option

from pokeapi_moves.lib import sh

cli = typer.Typer()


@cli.command()
def forms(
    alt_forms_lua: Annotated[str, Option(help="The path to AltForms-data.lua")],
):

    lua_export = sh(
        "lua", "-", input=LuaFormExport.lua_script(alt_forms_lua), pipe_stdio=False
    ).stdout
    alt_forms_json: list[LuaFormExport] = json.loads(
        lua_export, object_hook=LuaFormExport.from_json
    )
    alt_forms_sql_values = ", ".join(f.as_sql_row() for f in alt_forms_json)

    print(f"""
        select a.form_abbr, fn.name, f.*
        from pokemon_v2_pokemonform f
            join pkmn p on p.id = f.pokemon_id
            join pokemon_v2_pokemonformname fn on fn.pokemon_form_id = f.id
            join (
                select
                    a.column1 as form_abbr,
                    a.column2 as form_name,
                    a.column3 as form_ndex
                from (values {alt_forms_sql_values}) a
            ) a on fn.name = a.form_name
                and a.form_ndex = p.species_id
        where fn.language_id = 8
    """)


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
        return f"({s(self.abbr)}, {s(self.name)}, {self.ndex})"

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
