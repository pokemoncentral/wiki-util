from dataclasses import dataclass
from typing import Optional, Self, Tuple

from lib import convert_pokename, sanitize_lua_table_key, should_ignore


@dataclass
class Abilities:
    ability1: str
    ability2: str
    hidden_ability: str

    def to_poke_abil_data(self, key: str, ndex_key: str) -> str:
        ability2 = (
            f" ability2 = '{self.ability2}'," if self.ability1 != self.ability2 else ""
        )
        return f"""
t{key} = {{ability1 = '{self.ability1}',{ability2} abilityd = '{self.hidden_ability}'}}
t[{ndex_key}] = t{key}
""".strip()


@dataclass
class Stats:
    hp: int
    atk: int
    deff: int
    spatk: int
    spdef: int
    spe: int

    def to_poke_stats(self, key: str, ndex_key: str) -> str:
        return f"""
d{key} = {{hp = {self.hp}, atk = {self.atk}, def = {self.deff}, spatk = {self.spatk}, spdef = {self.spdef}, spe = {self.spe}}}
d[{ndex_key}] = d{key}
""".strip()


@dataclass
class Moves:
    level_up: list[Tuple[int, str]]
    tm: list[Tuple[str, str]]
    egg: list[str]
    reminder: list[str]


@dataclass
class Pkmn:
    lua_table_key: str
    lua_ndex_index: str
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
            abbr = normalized_name.removeprefix(sanitized_name.lower())
            ndex_key = f'"{ndex:04d}{abbr}"'
        except ValueError:
            sanitized_name = name
            ndex_key = ndex

        return (
            None
            if should_ignore(normalized_name)
            else cls(
                sanitize_lua_table_key(normalized_name),
                ndex_key,
                ndex,
                sanitized_name,
                types,
                stats,
                abilities,
                moves,
            )
        )

    def to_poke_data(self) -> str:
        type1 = self.types[0].lower()
        type2 = self.types[1].lower()
        match (type1, type2):
            case ("coleottero", "coleottero"):
                pass

            case ("coleottero", _):
                type1 = "coleot"

            case (_, "coleottero"):
                type2 = "coleot"

        return f"""
t{self.lua_table_key} = {{name = '{self.name}', ndex = {self.ndex}, type1 = '{type1}', type2 = '{type2}'}}
t[{self.lua_ndex_index}] = t{self.lua_table_key}
""".strip()

    def to_poke_abil_data(self) -> str:
        return self.abilities.to_poke_abil_data(self.lua_table_key, self.lua_ndex_index)

    def to_poke_stats(self) -> str:
        return self.stats.to_poke_stats(self.lua_table_key, self.lua_ndex_index)
