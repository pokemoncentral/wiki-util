# ruff: noqa: UP031

import itertools
import json
from collections.abc import Iterable
from dataclasses import dataclass
from sqlite3 import Cursor
from typing import Annotated, Self, cast

import typer
from typer import Argument, Option

from pokeapi_moves import pokeapi_db
from pokeapi_moves.lib import LearningMethod, named_args, to_ndex, wipe_db_help
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
    movelist_entries = list(
        pokeapi_db.query_file(
            sql_file,
            move=move,
            learning_method=learning_method,
            game=game,
            result_class=MovelistResult,
        )
    )

    parent_candidates = filter_parent_candidates(movelist_entries)

    for group_learning_method, by_learning_method in itertools.groupby(
        movelist_entries, lambda r: r.learning_method
    ):
        by_game = [
            (game, list(entries))
            for game, entries in itertools.groupby(by_learning_method, lambda r: r.game)
        ]
        movelists = [
            "{{#invoke: Movelist | learningMethod = %s | type = %s\n%s\n}}"
            % (
                group_learning_method,
                db_move.type,
                "\n".join(entry.to_wikicode(parent_candidates) for entry in entries),
            )
            for _, entries in by_game
        ]

        if len(movelists) == 1:
            print(movelists[0])
            continue

        print(make_tabs((game for game, _ in by_game), movelists))


type MovelistTupleResult = tuple[
    *PkmnResultTuple, LearningMethod, str, str, str | None, int, int, int, str, int
]


@dataclass(kw_only=True)
class MovelistResult(SqliteResultFactory[MovelistTupleResult]):
    pkmn: PkmnResult
    learning_method: LearningMethod
    game: str
    levels: list[int] | None
    machine: str | None
    stab: bool
    evo_stab: bool
    evo_chains_id: int
    stage_in_evo_chain: int | None
    is_baby: bool

    def to_wikicode(self, parents: Iterable[Self]) -> str:
        match self.learning_method:
            case "egg":
                tail = ",".join(map(str, self.find_parents(self, parents)))

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

        match (self.stab, self.evo_stab):
            case (True, _):
                apostrophes = "'''"

            case (False, True):
                apostrophes = "''"

            case _:
                apostrophes = None

        args = (
            to_ndex(self.pkmn.ndex),
            named_args(form=self.pkmn.form),
            tail,
            apostrophes,
            " //",
        )
        return "|" + "|".join(str(arg) for arg in args if arg is not None)

    @classmethod
    def from_sqlite_tuple(
        cls,
        cursor: Cursor,
        sqlite_tuple: MovelistTupleResult,
    ) -> Self:
        (
            learning_method,
            game,
            levels_json,
            machine,
            stab,
            evo_stab,
            evo_chains_id,
            evo_chains_json,
            is_baby,
        ) = sqlite_tuple[7:]

        pkmn = PkmnResult.from_sqlite_tuple(cursor, sqlite_tuple[:7])
        levels = sorted(set(cast(list[int], json.loads(levels_json))))
        chains = cast(list[list[int]], json.loads(evo_chains_json))
        return cls(
            pkmn=pkmn,
            learning_method=cast(LearningMethod, learning_method),
            game=game,
            levels=levels if len(levels) > 0 else None,
            machine=machine,
            stab=stab == 1,
            evo_stab=evo_stab == 1,
            evo_chains_id=evo_chains_id,
            stage_in_evo_chain=cls.find_stage_in_evo_chain(pkmn.ndex, chains),
            is_baby=is_baby == 1,
        )

    @classmethod
    def find_parents(cls, entry: Self, parents: Iterable[Self]) -> Iterable[int]:
        entry_egg_groups = {
            egg_group
            for egg_group in (entry.pkmn.egg_group1, entry.pkmn.egg_group2)
            if egg_group is not None
        }
        return sorted(
            {
                parent.pkmn.ndex
                for parent in parents
                if entry.game == parent.game
                and entry.evo_chains_id != parent.evo_chains_id
                and not entry_egg_groups.isdisjoint(
                    (parent.pkmn.egg_group1, parent.pkmn.egg_group2)
                )
            }
        )

    @staticmethod
    def find_stage_in_evo_chain(
        pkmn_id: int, evo_chains: list[list[int]]
    ) -> int | None:
        for c in evo_chains:
            try:
                return c.index(pkmn_id)
            except ValueError:
                pass
        return None


def filter_parent_candidates(resultset: list[MovelistResult]) -> list[MovelistResult]:
    parents = sorted(
        (
            parent
            for parent in resultset
            if not parent.is_baby
            and parent.learning_method != "egg"
            and parent.stage_in_evo_chain is not None
        ),
        key=lambda p: (p.evo_chains_id, p.stage_in_evo_chain),
    )

    return [
        # entries are already sorted by earliest stage in evolution chain
        next(evo_chain_entries)
        for _, evo_chain_entries in itertools.groupby(
            parents, key=lambda p: p.evo_chains_id
        )
    ]


def make_tabs(games: Iterable[str], movelists: Iterable[str]) -> str:
    header_items = (
        (
            '{{Tabs/headeritem|n=%d|class=text-center width-xl-10 width-lg-15 width-sm-20 width-xs-25|style=margin: 0.1em 0;|title=<div class="width-xl-100">{{#invoke: blackabbrev | %s}}</div>}}'
            % (idx, game)
        )
        for idx, game in enumerate(games)
    )
    body_items = (
        "{{Tabs/item|n=%d|content=%s}}" % (idx, movelist)
        for idx, movelist in enumerate(movelists)
    )

    return "\n".join(
        (
            "{{Tabs/header|style=roundy|class=tabs-grad-border|labelborder=0.3em solid|containerstyle=--tabs-border-grad: linear-gradient(to right, #91A119, #81B9EF);|headerclass=flex flex-items-center flex-main-space-around flex-wrap|headerstyle=gap: 0.1px;}}",
            *header_items,
            "{{Tabs/body}}",
            *body_items,
            "{{Tabs/footer}}",
        )
    )
