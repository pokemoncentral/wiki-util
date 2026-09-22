import os
import sqlite3
from subprocess import CompletedProcess

from pokeapi_moves import paths
from pokeapi_moves.lib import PathOrStr, sh

db_file = os.path.join(paths.pokeapi, "db.sqlite3")
db_min_size_bytes = 50 * 2**20


def ensure_db(*, wipe_db: bool = False):
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


def query_db(file: PathOrStr):
    with open(file, "r", encoding="utf-8") as sql_file:
        sql = sql_file.read()

    db = sqlite3.connect(db_file)
    cursor = db.cursor()
    for row in cursor.execute(sql):
        print(row)


def pokeapi_make(*args: str) -> CompletedProcess[bytes]:
    return sh("make", *args, cwd=paths.pokeapi)
