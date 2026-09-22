import shutil
import subprocess
from os import PathLike

type PathOrStr = PathLike | str


def sh(
    bin: PathOrStr, *args: str, cwd: PathOrStr | None = None
) -> subprocess.CompletedProcess[bytes]:
    bin_path = shutil.which(bin)
    if bin_path is None:
        raise ValueError(f"Binary {bin} not found on PATH")
    return subprocess.run((bin_path, *args), cwd=cwd, check=True, shell=False)
