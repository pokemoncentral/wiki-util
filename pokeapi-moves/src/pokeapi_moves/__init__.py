import sys

from pokeapi_moves import pokeapi_lib
from pokeapi_moves.movelist import movelist


def main():
    pokeapi_lib.ensure_db(wipe_db="--wipe-db" in sys.argv[1:])
    match sys.argv[1]:
        case "movelist":
            movelist(move="superpower", learning_method="tutor", game="platinum")
