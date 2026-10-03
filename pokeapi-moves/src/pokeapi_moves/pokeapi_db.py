import os
import sqlite3
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from sqlite3 import Cursor
from subprocess import CompletedProcess
from typing import Any, Literal, Self

from pokeapi_moves import paths
from pokeapi_moves.lib import PathOrStr, sh

db_file = os.path.join(paths.pokeapi, "db.sqlite3")
db_min_size_bytes = 50 * 2**20

utils_dir = os.path.join(paths.queries, "utils")
util_files = sorted(
    sql_file.path
    for sql_file in os.scandir(utils_dir)
    if sql_file.is_file() and sql_file.name.endswith(".sql")
)


class SqliteResultFactory[TSqlTuple: tuple[Any, ...]](ABC):
    @classmethod
    @abstractmethod
    def from_sqlite_tuple(cls, cursor: Cursor, sqlite_tuple: TSqlTuple) -> Self: ...


type PkmnResultTuple = tuple[int, str, str, str, str | None, str, str | None]


@dataclass(kw_only=True)
class PkmnResult(SqliteResultFactory[PkmnResultTuple]):
    ndex: int
    name: str
    form: str | None
    type1: str
    type2: str | None
    egg_group1: str
    egg_group2: str | None

    @classmethod
    def from_sqlite_tuple(cls, cursor: Cursor, sqlite_tuple: PkmnResultTuple) -> Self:
        ndex, name, form, type1, type2, egg_group1, egg_group2 = sqlite_tuple
        return cls(
            ndex=ndex,
            name=name,
            form=form,
            type1=type1,
            type2=type2,
            egg_group1=egg_group1,
            egg_group2=egg_group2,
        )


type MoveResultTuple = tuple[int, str, str]


@dataclass(kw_only=True)
class MoveResult(SqliteResultFactory[MoveResultTuple]):
    id: int
    name: str
    type: str

    @classmethod
    def from_sqlite_tuple(cls, cursor: Cursor, sqlite_tuple: MoveResultTuple) -> Self:
        id, name, type = sqlite_tuple
        return cls(id=id, name=name, type=type)


def ensure(*, wipe_db: bool | Literal["all"] = False):
    # These are fast, no need to skip calling them if not necessary
    pokeapi_make("install")
    if wipe_db == "all":
        pokeapi_make("wipe-sqlite-db")
    pokeapi_make("setup")

    try:
        should_build_db = os.path.getsize(db_file) < db_min_size_bytes
    except OSError:
        # Db file doesn't exist at all
        should_build_db = True

    if should_build_db:
        pokeapi_make("build-db")
    if should_build_db or wipe_db != False:
        utils()


def pokeapi_make(*args: str) -> CompletedProcess[str]:
    return sh("make", *args, cwd=paths.pokeapi)


def query_file[TResult: SqliteResultFactory](
    file: PathOrStr,
    *,
    result_class: type[TResult] | None = None,
    **sql_params: str | None,
) -> Iterator[TResult]:
    with open(os.path.join(paths.queries, file), "r", encoding="utf-8") as sql:
        return query_str(sql.read(), result_class=result_class, **sql_params)


def query_str[TResult: SqliteResultFactory](
    sql: str,
    *,
    result_class: type[TResult] | None = None,
    **sql_params: str | None,
) -> Iterator[TResult]:
    db = sqlite3.connect(db_file)
    if result_class is not None:
        db.row_factory = result_class.from_sqlite_tuple
    return db.cursor().execute(sql, sql_params)


def query_move(move: str) -> MoveResult:
    return next(
        query_str(
            """
            select id, it_name as name, type_it_name as type
            from move
            where name = :move
            """,
            result_class=MoveResult,
            move=move,
        )
    )


def utils():
    db = sqlite3.connect(db_file)
    cursor = db.cursor()
    for file_path in util_files:
        with open(file_path, "r", encoding="utf-8") as util_file:
            cursor.executescript(util_file.read())
