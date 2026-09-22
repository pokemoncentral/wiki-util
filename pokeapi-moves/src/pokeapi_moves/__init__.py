import sys

from pokeapi_moves import pokeapi_lib


def main():
    pokeapi_lib.ensure_db(wipe_db="--wipe-db" in sys.argv[1:])
