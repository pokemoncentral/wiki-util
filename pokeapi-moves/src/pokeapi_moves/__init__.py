import typer

from pokeapi_moves.db_gen import cli as generate
from pokeapi_moves.movelist import cli as movelist

cli = typer.Typer()
cli.add_typer(movelist)
cli.add_typer(generate, name="db-gen")
