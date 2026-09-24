import itertools
import json
from dataclasses import dataclass
from sqlite3 import Cursor
from typing import Annotated, Self, cast

import typer
from typer import Argument, Option

from pokeapi_moves import pokeapi_db
from pokeapi_moves.lib import LearningMethod, replace_none, to_ndex, wipe_db_help
from pokeapi_moves.pokeapi_db import PkmnResult, PkmnResultTuple, SqliteResultFactory

sql_file = "movelist.sql"

cli = typer.Typer()


@cli.command()
def movelist(
    move: Annotated[
        str,
        Argument(
            help="The ENGLISH name of move to generate the Movelist module call for"
        ),
    ],
    learning_method: Annotated[
        str | None,
        Option(
            help="The learning method for the Movelist module call. If omitted, generate calls for all available learning methods of the move"
        ),
    ] = None,
    game: Annotated[
        str | None,
        Option(
            help="The game for the Movelist module call. If omitted, generate tabs and module calls for all games the move is available in"
        ),
    ] = None,
    wipe_db: Annotated[bool, Option(help=wipe_db_help)] = False,
):
    """
    Generate the movelist module call in WikiCode
    """

    pokeapi_db.ensure(wipe_db=wipe_db)
    db_move = pokeapi_db.query_move(move)
    movelist_entries = pokeapi_db.query_file(
        sql_file, move, learning_method, game, result_class=MovelistResult
    )

    for group_learning_method, by_learning_method in itertools.groupby(
        movelist_entries, lambda r: r.learning_method
    ):
        print(
            "{{#invoke: Movelist | learningMethod = %s | type = %s"  # noqa: UP031
            % (group_learning_method, db_move.type)
        )
        for group_game, by_game in itertools.groupby(
            by_learning_method, lambda r: r.game
        ):
            for entry in by_game:
                print(entry.to_wikicode())
        print("}}")


type MovelistTupleResult = tuple[*PkmnResultTuple, LearningMethod, str, str, str | None]


@dataclass(kw_only=True)
class MovelistResult(SqliteResultFactory[MovelistTupleResult]):
    pkmn: PkmnResult
    learning_method: LearningMethod
    game: str
    levels: list[int] | None
    machine: str | None

    def to_wikicode(self) -> str:
        match self.learning_method:
            case "level-up":
                assert self.levels is not None
                tail = ", ".join(map(str, self.levels))

            case "machine":
                assert self.machine is not None
                tail = self.machine

            case "tutor":
                tail = None

            case _:
                raise ValueError(f"Uknown LearningMethod: {self.learning_method}")

        args = (
            to_ndex(self.pkmn.id),
            self.pkmn.name,
            self.pkmn.type1,
            replace_none(self.pkmn.type2),
            self.pkmn.egg_group1,
            replace_none(self.pkmn.egg_group2),
            tail,
            "//",
        )
        return "|".join(str(arg) for arg in args if arg is not None)

    @classmethod
    def from_sqlite_tuple(
        cls,
        cursor: Cursor,
        sqlite_tuple: MovelistTupleResult,
    ) -> Self:
        learning_method, game, levels_json, machine = sqlite_tuple[6:]
        levels = json.loads(levels_json)
        return cls(
            pkmn=PkmnResult.from_sqlite_tuple(cursor, sqlite_tuple[:6]),
            learning_method=cast(LearningMethod, learning_method),
            game=game,
            levels=levels if len(levels) > 0 else None,
            machine=machine,
        )
