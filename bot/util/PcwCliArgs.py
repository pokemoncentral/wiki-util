import itertools
import sys
import textwrap
from dataclasses import dataclass
from typing import Optional, Self


@dataclass
class Arg:
    pos: int
    default: Optional[str]
    doc_name: str

    @property
    def is_required(self) -> bool:
        return self.default is None


@dataclass
class Opt:
    name: str
    default: Optional[str | bool]
    is_flag: bool = False

    @property
    def is_required(self) -> bool:
        return self.default is None

    @property
    def doc_name(self) -> str:
        return "-" + self.name


class PcwCliArgs:
    args: dict[str, Arg]
    opts: dict[str, Opt]

    def __init__(self, *, include_pwb: bool = False):
        self.args = {}
        self.opts = {"help": Opt("help", is_flag=True, default=False)}

    def flag(self, name: str, *, required: bool = False) -> Self:
        if name in self.opts:
            raise ValueError(f"Flag '{name}' is already defined")

        self.opts[name] = Opt(name, is_flag=True, default=None if required else False)
        return self

    def opt(self, name: str, *, default: Optional[str] = None) -> Self:
        if name in self.opts:
            raise ValueError(f"Option '{name}' is already defined")

        self.opts[name] = Opt(name, default)
        return self

    def pos(self, doc_name: str, *, default: Optional[str] = None) -> Self:
        if doc_name in self.args:
            raise ValueError(f"Positional argument '{doc_name}' is already defined")

        self.args[doc_name] = Arg(len(self.args), default, doc_name)
        return self

    def parse(self, args: Optional[list[str]] = None) -> dict[str, str]:
        args = args or sys.argv[1:]

        pos_args_index = 0
        res = {}
        for cli_arg in args:
            if cli_arg.startswith("-"):
                name, _, value = cli_arg[1:].partition(":")

                try:
                    opt = self.opts[name]
                except KeyError:
                    self._user_facing_error(f"Unknown option: -{name}", exit_code=31)
                if not value and not opt.is_flag:
                    self._user_facing_error(
                        f"A value is required for option {opt.doc_name}", exit_code=30
                    )

                res[opt.name] = True if opt.is_flag else value

            else:
                pos_arg = next(
                    (a for a in self.args.values() if a.pos == pos_args_index), None
                )
                if pos_arg is None:
                    self._user_facing_error(
                        f"Unknown argument at position #{pos_args_index + 1}: {cli_arg}"
                    )

                pos_args_index += 1
                res[pos_arg.doc_name] = cli_arg

        missing_cli_args = list(
            itertools.chain(
                (
                    a
                    for a in self.args.values()
                    if a.is_required and a.doc_name not in res
                ),
                (o for o in self.opts.values() if o.is_required and o.name not in res),
            )
        )

        if missing_cli_args:
            self._user_facing_error(
                f"""
                Missing arguments:{"\n".join(a.doc_name for a in missing_cli_args)}
                """
            )

        return res

    @staticmethod
    def _user_facing_error(msg: str, *, exit_code: int = 1):
        print(textwrap.dedent(msg.strip()), file=sys.stderr)
        sys.exit(exit_code)
