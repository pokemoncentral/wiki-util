import json
from dataclasses import dataclass
from sqlite3 import Cursor
from typing import Self, cast

from pokeapi_moves import pokeapi_lib
from pokeapi_moves.lib import LearningMethod, PkmnResult, SqliteResultFactory

sql_file = "movelist.sql"


def movelist(
    *,
    move: str | None = None,
    learning_method: str | None = None,
    game: str | None = None,
):
    rows = pokeapi_lib.query_db(
        sql_file, move, learning_method, game, result_class=MovelistResult
    )
    for row in rows:
        print(row)


type MovelistTupleResult = tuple[int, str, str, str | None, LearningMethod, bytes]


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
