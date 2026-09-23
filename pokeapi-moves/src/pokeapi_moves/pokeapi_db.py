import os
import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from sqlite3 import Cursor
from subprocess import CompletedProcess
from typing import Any, Self

from pokeapi_moves import paths
from pokeapi_moves.lib import PathOrStr, sh

db_file = os.path.join(paths.pokeapi, "db.sqlite3")
db_min_size_bytes = 50 * 2**20

sql_lib_file = "lib.sql"


class SqliteResultFactory[TSqlTuple: tuple[Any, ...]](ABC):
    @classmethod
    @abstractmethod
    def from_sqlite_tuple(cls, cursor: Cursor, sqlite_tuple: TSqlTuple) -> Self: ...


@dataclass(kw_only=True)
class PkmnResult(SqliteResultFactory[tuple[int, str, str, str | None]]):
    id: int
    name: str
    type1: str
    type2: str | None

    @classmethod
    def from_sqlite_tuple(
        cls, cursor: Cursor, sqlite_tuple: tuple[int, str, str, str | None]
    ) -> Self:
        id, name, type1, type2 = sqlite_tuple
        return cls(id=id, name=name, type1=type1, type2=type2)


@dataclass(kw_only=True)
class MoveResult(SqliteResultFactory[tuple[int, str, str]]):
    id: int
    name: str
    type: str

    @classmethod
    def from_sqlite_tuple(
        cls, cursor: Cursor, sqlite_tuple: tuple[int, str, str]
    ) -> Self:
        id, name, type = sqlite_tuple
        return cls(id=id, name=name, type=type)


def ensure(*, wipe_db=False):
    # These are fast, no need to skip calling them if not necessary
    pokeapi_make("install")
    pokeapi_make("setup")

    try:
        should_build_db = wipe_db or os.path.getsize(db_file) < db_min_size_bytes
    except OSError:
        # Db file doesn't exist at all
        should_build_db = True
    if should_build_db:
        pokeapi_make("build-db")


def load_query_file(file: PathOrStr) -> str:
    with open(os.path.join(paths.queries, file), "r", encoding="utf-8") as sql_file:
        return sql_file.read()


def pokeapi_make(*args: str) -> CompletedProcess[bytes]:
    return sh("make", *args, cwd=paths.pokeapi)


def query_file[TResult: SqliteResultFactory](
    file: PathOrStr,
    *args: str | None,
    with_lib=True,
    result_class: type[TResult] | None = None,
) -> Iterator[TResult]:
    return query_str(
        load_query_file(file), *args, with_lib=with_lib, result_class=result_class
    )


def query_str[TResult: SqliteResultFactory](
    sql: str,
    *args: str | None,
    with_lib=True,
    result_class: type[TResult] | None = None,
) -> Iterator[TResult]:
    db = sqlite3.connect(db_file)
    if result_class is not None:
        db.row_factory = result_class.from_sqlite_tuple
    cursor = db.cursor()

    if with_lib:
        cursor.executescript(load_query_file(sql_lib_file))

    return cursor.execute(sql, args)


def query_move(move: str) -> MoveResult:
    return next(
        query_str(
            """
            select id, it_name as name, type_it_name as type
            from move
            where name = ?
            """,
            move,
            result_class=MoveResult,
        )
    )
