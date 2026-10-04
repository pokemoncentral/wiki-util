import json
import os
import textwrap
from dataclasses import dataclass
from typing import Annotated, Any, ClassVar, Self

import typer
from typer import Option

from pokeapi_moves import pokeapi_db
from pokeapi_moves.lib import generated_files_marker, sh, to_sql

type JSONObject = dict[str, Any]

forms_sql_output = os.path.join(
    pokeapi_db.utils_dir, f"01-{generated_files_marker}-forms.sql"
)

cli = typer.Typer()


@cli.command(help="Generate SQL from Pokémon Central Wiki `AltForms-data.lua`")
def forms(
    alt_forms_lua: Annotated[str, Option(help="The path to `AltForms-data.lua`")],
    output: Annotated[
        str | None,
        Option(help="The generated SQL file path. Mostly useful in tests"),
    ] = None,
):
    lua_export = sh(
        "lua", "-", input=LuaFormExport.lua_script(alt_forms_lua), pipe_stdio=False
    ).stdout
    alt_forms_json: list[LuaFormExport] = json.loads(
        lua_export, object_hook=LuaFormExport.from_json
    )
    alt_forms_sql_values = f",\n{4 * 4 * ' '}".join(
        f.as_sql_row() for f in alt_forms_json
    )

    sql_output = forms_sql_output if output is None else output
    with open(sql_output, "w", encoding="utf-8") as forms_sql:
        forms_sql.write(textwrap.dedent(f"""
            drop table if exists lua_forms_export;
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
            """.strip("\n")))


@dataclass(kw_only=True)
class LuaFormExport:
    abbr: str
    name: str
    ndex: int

    lua_var: ClassVar[str] = "altForms"

    def as_sql_row(self) -> str:
        cols = map(to_sql, (self.name, self.abbr, self.ndex))
        return f"({', '.join(cols)})"

    @classmethod
    def from_json(cls, json_dict: JSONObject) -> Self | JSONObject:
        try:
            return cls(**json_dict)
        except TypeError:
            # JSON property names don't match class fields
            return json_dict

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


def require_lua(target_var: str, file: str) -> str:
    parent, file_name = os.path.split(file)
    extensionless, _ = os.path.splitext(file_name)
    return f"""
        package.path = '{parent}/?.lua;' .. package.path
        local {target_var} = require('{extensionless}')
    """
