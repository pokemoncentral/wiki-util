import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from os import PathLike
from sqlite3 import Cursor
from typing import Any, Literal, Self

type LearningMethod = Literal["level-up", "tutor"]

type PathOrStr = PathLike | str

wipe_db_help = "Wipe the PokéAPI database, and recreate it from the CSV files"


@dataclass(kw_only=True)
class PkmnResult:
    id: int
    name: str
    type1: str
    type2: str | None


class SqliteResultFactory[TSqlTuple: tuple[Any, ...]](ABC):
    @classmethod
    @abstractmethod
    def from_sqlite_tuple(cls, cursor: Cursor, sqlite_tuple: TSqlTuple) -> Self: ...


def sh(
    bin: PathOrStr, *args: str, cwd: PathOrStr | None = None
) -> subprocess.CompletedProcess[bytes]:
    bin_path = shutil.which(bin)
    if bin_path is None:
        raise ValueError(f"Binary {bin} not found on PATH")
    return subprocess.run((bin_path, *args), cwd=cwd, check=True, shell=False)
