import json
from dataclasses import dataclass
from sqlite3 import Cursor
from typing import Annotated, Self, cast

import typer
from typer import Argument, Option

from pokeapi_moves import pokeapi_lib
from pokeapi_moves.lib import (
    LearningMethod,
    PkmnResult,
    SqliteResultFactory,
    wipe_db_help,
)

sql_file = "movelist.sql"

cli = typer.Typer()


@cli.command()
def movelist(
    move: Annotated[
        str,
        Argument(
            help="The ENGLISH name of move to generate the Movelist module call for"
        ),
    ],
    learning_method: Annotated[
        str | None,
        Option(
            help="The learning method for the Movelist module call. If omitted, generate calls for all available learning methods of the move"
        ),
    ] = None,
    game: Annotated[
        str | None,
        Option(
            help="The game for the Movelist module call. If omitted, generate tabs and module calls for all games the move is available in"
        ),
    ] = None,
    wipe_db: Annotated[bool, Option(help=wipe_db_help)] = False,
):
    """
    Generate the movelist module call in WikiCode
    """
    pokeapi_lib.ensure_db(wipe_db=wipe_db)
    rows = pokeapi_lib.query_db(
        sql_file, move, learning_method, game, result_class=MovelistResult
    )
    for row in rows:
        print(row)


type MovelistTupleResult = tuple[int, str, str, str | None, LearningMethod, str]


@dataclass(kw_only=True)
class MovelistResult(SqliteResultFactory[MovelistTupleResult]):
    pkmn: PkmnResult
    learning_method: LearningMethod
    levels: list[int] | None

    @classmethod
    def from_sqlite_tuple(
        cls,
        cursor: Cursor,
        sqlite_tuple: MovelistTupleResult,
    ) -> Self:
        levels = json.loads(sqlite_tuple[5])
        return cls(
            pkmn=PkmnResult(
                id=sqlite_tuple[0],
                name=sqlite_tuple[1],
                type1=sqlite_tuple[2],
                type2=sqlite_tuple[3],
            ),
            learning_method=cast(LearningMethod, sqlite_tuple[4]),
            levels=levels if len(levels) > 0 else None,
        )
