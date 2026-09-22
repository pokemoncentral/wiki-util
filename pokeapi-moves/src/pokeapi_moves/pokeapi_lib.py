import os
import sqlite3
from collections.abc import Iterable
from subprocess import CompletedProcess

from pokeapi_moves import paths
from pokeapi_moves.lib import PathOrStr, SqliteResultFactory, sh

db_file = os.path.join(paths.pokeapi, "db.sqlite3")
db_min_size_bytes = 50 * 2**20

sql_lib_file = "lib.sql"


def ensure_db(*, wipe_db=False):
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


def query_db[
    TResult: SqliteResultFactory,
](
    file: PathOrStr,
    *args: str | None,
    with_lib=True,
    result_class: type[TResult] | None = None,
) -> Iterable[type[TResult]]:
    db = sqlite3.connect(db_file)
    if result_class is not None:
        db.row_factory = result_class.from_sqlite_tuple
    cursor = db.cursor()

    if with_lib:
        cursor.executescript(load_query_file(sql_lib_file))

    return cursor.execute(load_query_file(file), args)
