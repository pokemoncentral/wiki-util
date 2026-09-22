from pokeapi_moves import pokeapi_lib

sql_file = "movelist.sql"


def movelist(*, move: str, learning_method: str, game: str):
    pokeapi_lib.query_db(sql_file, move, learning_method, game)
