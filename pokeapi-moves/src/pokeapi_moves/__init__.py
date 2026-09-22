import typer

from pokeapi_moves.movelist import cli as movelist

cli = typer.Typer()
cli.add_typer(movelist)
