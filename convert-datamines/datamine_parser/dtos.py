from dataclasses import dataclass
from typing import Optional, Self, Tuple

from lib import convert_pokename, sanitize_lua_table_key, should_ignore


@dataclass
class Abilities:
    ability1: str
    ability2: str
    hidden_ability: str

    def to_poke_abil_data(self, key: str) -> str:
        return f"t{key} = {{ability1 = '{self.ability1}', ability2 = '{self.ability1}', abilityd = '{self.hidden_ability}'}}"


@dataclass
class Stats:
    hp: int
    atk: int
    deff: int
    spatk: int
    spdef: int
    spe: int

    def to_poke_stats(self, key: str) -> str:
        return f"d{key} = {{hp = {self.hp}, atk = {self.atk}, def = {self.deff}, spatk = {self.spatk}, spdef = {self.spdef}, spe = {self.spe}}}"


@dataclass
class Moves:
    level_up: list[Tuple[int, str]]
    tm: list[Tuple[str, str]]
    egg: list[str]
    reminder: list[str]

    def to_learnlist(self) -> str:
        return "yoho"


@dataclass
class Pkmn:
    lua_table_key: str
    ndex: int
    name: str
    types: Tuple[str, str]
    stats: Stats
    abilities: Abilities
    moves: Moves

    @classmethod
    def create(
        cls,
        ndex: int,
        name: str,
        types: Tuple[str, str],
        stats: Stats,
        abilities: Abilities,
        moves: Moves,
    ) -> Optional[Self]:
        normalized_name = convert_pokename(name)
        try:
            int(name[-2:])
            sanitized_name = name[:-2]
        except ValueError:
            sanitized_name = name
        return (
            None
            if should_ignore(normalized_name)
            else cls(
                sanitize_lua_table_key(normalized_name),
                ndex,
                sanitized_name,
                types,
                stats,
                abilities,
                moves,
            )
        )

    def to_poke_data(self) -> str:
        return f"t{self.lua_table_key} = {{name = '{self.name}', ndex = {self.ndex}, type1 = '{self.types[0]}', type2 = '{self.types[1]}'}}"

    def to_poke_abil_data(self) -> str:
        return self.abilities.to_poke_abil_data(self.lua_table_key)

    def to_poke_stats(self) -> str:
        return self.stats.to_poke_stats(self.lua_table_key)

    def to_learnlist(self) -> str:
        return self.moves.to_learnlist()
        return self.moves.to_learnlist()
