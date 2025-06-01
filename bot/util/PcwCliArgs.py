import itertools
import os
import sys
import textwrap
from dataclasses import dataclass
from functools import partial
from operator import attrgetter
from typing import Optional, Self


@dataclass(kw_only=True)
class Arg:
    pos: int
    doc_name: str
    desc: str
    default: Optional[str] = None

    sort_key = attrgetter("pos")

    @property
    def is_required(self) -> bool:
        return self.default is None


@dataclass(kw_only=True)
class Opt:
    name: str
    desc: str
    value_name: Optional[str] = None
    default: Optional[str | bool] = None

    sort_key = attrgetter("name")

    @property
    def is_flag(self) -> bool:
        return self.value_name is None

    @property
    def is_required(self) -> bool:
        return self.default is None

    @property
    def doc_name(self) -> str:
        return (
            f"-{self.name}"
            if self.value_name is None
            else f"-{self.name}:<{self.value_name}>"
        )


class PcwCliArgs:
    args: dict[str, Arg]
    opts: dict[str, Opt]

    INDENT_SIZE = 4
    _help_opt = Opt(name="help", desc="Show this help text", default=False)

    def __init__(self, *, include_pwb: bool = False):
        self.args = {}
        self.opts = {self._help_opt.name: self._help_opt}

    def flag(self, name: str, desc: str, *, required: bool = False) -> Self:
        if name in self.opts:
            raise ValueError(f"Flag '{name}' is already defined")

        self.opts[name] = Opt(name=name, desc=desc, default=None if required else False)
        return self

    def opt(
        self, name: str, value_name: str, desc: str, *, default: Optional[str] = None
    ) -> Self:
        if name in self.opts:
            raise ValueError(f"Option '{name}' is already defined")

        self.opts[name] = Opt(
            name=name, value_name=value_name, desc=desc, default=default
        )
        return self

    def pos(self, doc_name: str, desc: str, *, default: Optional[str] = None) -> Self:
        if doc_name in self.args:
            raise ValueError(f"Positional argument '{doc_name}' is already defined")

        self.args[doc_name] = Arg(
            pos=len(self.args), doc_name=doc_name, desc=desc, default=default
        )
        return self

    def parse(self, args: Optional[list[str]] = None) -> dict[str, str]:
        args = args or sys.argv[1:]

        if self._help_opt.doc_name in args:
            print(self.help())
            sys.exit(0)

        pos_args_index = 0
        res = {}
        for cli_arg in map(str.strip, args):
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
                Missing arguments:{os.linesep.join(a.doc_name for a in missing_cli_args)}
                """
            )

        return res

    def help(self) -> str:
        arg_opt_sep = f"{os.linesep * 2}{" " * self.INDENT_SIZE * 4}"

        args = sorted(self.args.values(), key=Arg.sort_key)
        opts = sorted(self.opts.values(), key=Opt.sort_key)

        max_name_len = max(len(a.doc_name) for a in itertools.chain(args, opts))
        max_name_len += self.INDENT_SIZE - max_name_len % self.INDENT_SIZE

        return self._dedent(
            f"""
            {__doc__}

            Arguments:

                {arg_opt_sep.join(map(partial(self._arg_help, max_name_len), args))}

            Options:

                {arg_opt_sep.join(map(partial(self._arg_help, max_name_len), opts))}
            """
        )

    @staticmethod
    def _arg_help(max_name_len: int, a: Arg | Opt) -> str:
        name = f"\033[1m{a.doc_name}\033[0m"  # bold text
        separator = " " * (max_name_len - len(a.doc_name))
        return f"{name}{separator}{a.desc}."

    @classmethod
    def _user_facing_error(cls, msg: str, *, exit_code: int = 1):
        print(cls._dedent(msg), file=sys.stderr)
        sys.exit(exit_code)

    @staticmethod
    def _dedent(text: str) -> str:
        return textwrap.dedent(text).strip()
