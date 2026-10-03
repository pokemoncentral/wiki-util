import shutil
import subprocess
from os import PathLike
from typing import Any, Literal

type LearningMethod = Literal["egg", "level-up", "machine", "tutor"]

type PathOrStr = PathLike | str

generated_files_marker = "__generated__"


def named_args(**args: Any) -> str | None:
    wikicode_args = [
        f"{name} = {value}" for name, value in args.items() if value is not None
    ]
    return " | ".join(wikicode_args) if wikicode_args else None


def replace_none(value: Any, if_none: str = "") -> str:
    return if_none if value is None else str(value)


def sh(
    bin: PathOrStr,
    *args: str,
    cwd: PathOrStr | None = None,
    input: str | None = None,
    pipe_stdio=True,
) -> subprocess.CompletedProcess[str]:
    bin_path = shutil.which(bin)
    if bin_path is None:
        raise ValueError(f"Binary {bin} not found on PATH")
    return subprocess.run(
        (bin_path, *args),
        capture_output=not pipe_stdio,
        check=True,
        cwd=cwd,
        input=input,
        shell=False,
        text=True,
    )


def to_ndex(ndex_number: int) -> str:
    return f"""{ndex_number:04d}"""
