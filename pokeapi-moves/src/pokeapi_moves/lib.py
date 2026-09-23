import shutil
import subprocess
from os import PathLike
from typing import Any, Literal

type LearningMethod = Literal["egg", "level-up", "tutor"]

type PathOrStr = PathLike | str

wipe_db_help = "Wipe the PokéAPI database, and recreate it from the CSV files"


def sh(
    bin: PathOrStr, *args: str, cwd: PathOrStr | None = None
) -> subprocess.CompletedProcess[bytes]:
    bin_path = shutil.which(bin)
    if bin_path is None:
        raise ValueError(f"Binary {bin} not found on PATH")
    return subprocess.run((bin_path, *args), cwd=cwd, check=True, shell=False)


def replace_none(value: Any, if_none: str = "") -> str:
    return if_none if value is None else str(value)


def to_ndex(ndex_number: int) -> str:
    return f"""{ndex_number:04d}"""
