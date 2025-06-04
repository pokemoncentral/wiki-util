import itertools
import os
import sys
import textwrap
from dataclasses import dataclass
from functools import partial
from operator import attrgetter
from typing import Optional, Self

import pywikibot as pwb


@dataclass(kw_only=True)
class Arg:
    pos: int
    doc_name: str
    desc: str
    default: Optional[str] = None
    default_desc: Optional[str] = None

    sort_key = attrgetter("pos")

    @property
    def is_required(self) -> bool:
        return self.default_desc is None and self.default is None


@dataclass(kw_only=True)
class Opt:
    name: str
    desc: str
    value_name: Optional[str] = None
    default: Optional[str | bool] = None
    default_desc: Optional[str] = None

    sort_key = attrgetter("name")

    @property
    def is_flag(self) -> bool:
        return self.value_name is None

    @property
    def is_required(self) -> bool:
        return self.default_desc is None and self.default is None

    @property
    def doc_name(self) -> str:
        return (
            f"-{self.name}"
            if self.value_name is None
            else f"-{self.name}:<{self.value_name}>"
        )


class PcwCliArgs:
    _args: dict[str, Arg]
    _opts: dict[str, Opt]
    _include_pwb: bool
    _desc: bool

    INDENT_SIZE = 4
    _help_opt = Opt(name="help", desc="Show this help text", default=False)

    def __init__(self, description: str, *, include_pwb: bool = False):
        self._args = {}
        self._opts = {self._help_opt.name: self._help_opt}
        self._include_pwb = include_pwb
        self._desc = description

    def flag(
        self,
        name: str,
        desc: str,
        *,
        required: bool = False,
        default_desc: Optional[str] = None,
    ) -> Self:
        if name in self._opts:
            raise ValueError(f"Flag '{name}' is already defined")

        self._opts[name] = Opt(
            name=name,
            desc=desc,
            default=None if required else False,
            default_desc=default_desc,
        )
        return self

    def opt(
        self,
        name: str,
        value_name: str,
        desc: str,
        *,
        default: Optional[str] = None,
        default_desc: Optional[str] = None,
    ) -> Self:
        if name in self._opts:
            raise ValueError(f"Option '{name}' is already defined")

        self._opts[name] = Opt(
            name=name,
            value_name=value_name,
            desc=desc,
            default=default,
            default_desc=default_desc,
        )
        return self

    def pos(
        self,
        doc_name: str,
        desc: str,
        *,
        default: Optional[str] = None,
        default_desc: Optional[str] = None,
    ) -> Self:
        if doc_name in self._args:
            raise ValueError(f"Positional argument '{doc_name}' is already defined")

        self._args[doc_name] = Arg(
            pos=len(self._args),
            doc_name=doc_name,
            desc=desc,
            default=default,
            default_desc=default_desc,
        )
        return self

    def parse(self, args: Optional[list[str]] = None) -> dict[str, str]:
        args = args or sys.argv[1:]

        if self._help_opt.doc_name in args:
            print(self.help())
            sys.exit(0)

        if self._include_pwb:
            args = pwb.handle_args(args, do_help=False)

        pos_args_index = 0
        res = {
            a.name: a.default
            for a in itertools.chain(self._args.values(), self._opts.values())
            if not a.is_required
        }
        for cli_arg in map(str.strip, args):
            if cli_arg.startswith("-"):
                name, _, value = cli_arg[1:].partition(":")

                try:
                    opt = self._opts[name]
                except KeyError:
                    self._user_facing_error(f"Unknown option: -{name}", exit_code=31)
                if not value and not opt.is_flag:
                    self._user_facing_error(
                        f"A value is required for option {opt.doc_name}", exit_code=30
                    )

                res[opt.name] = True if opt.is_flag else value

            else:
                pos_arg = next(
                    (a for a in self._args.values() if a.pos == pos_args_index), None
                )
                if pos_arg is None:
                    self._user_facing_error(
                        f"Unknown argument at position #{pos_args_index + 1}: {cli_arg}"
                    )

                pos_args_index += 1
                res[pos_arg.doc_name] = cli_arg

        missing_arg_names = {
            *(a.doc_name for a in self._args.values()),
            *(o.name for o in self._opts.values()),
        }.difference(res.keys())

        if missing_arg_names:
            self._user_facing_error(
                f"""
                Missing arguments:{os.linesep.join(missing_arg_names)}
                """
            )

        return res

    def help(self) -> str:
        if not self._args and not self._opts:
            return self._dedent(self._desc)

        args = sorted(self._args.values(), key=Arg.sort_key)
        opts = sorted(self._opts.values(), key=Opt.sort_key)

        help_text = [self._dedent(self._desc)]

        max_name_len = max((len(a.doc_name) for a in itertools.chain(args, opts)))
        max_name_len += self.INDENT_SIZE - max_name_len % self.INDENT_SIZE

        if self._args:
            help_text += ("", "Arguments:")
            help_text += map(partial(self._arg_help, max_name_len), args)

        if self._opts:
            help_text += ("", "Options:")
            help_text += map(partial(self._arg_help, max_name_len), opts)

        return os.linesep.join(help_text)

    @classmethod
    def _arg_help(cls, max_name_len: int, a: Arg | Opt) -> str:
        indent = " " * cls.INDENT_SIZE
        name = f"\033[1m{a.doc_name}\033[0m"  # bold text
        separator = " " * (max_name_len - len(a.doc_name))

        if a.is_required or a.name == cls._help_opt.name:
            default = ""
        elif isinstance(a.default, bool):
            default_desc = "" if a.default_desc is None else ", " + a.default_desc
            default = f" \033[33mOptional\033[0m{default_desc}."
        else:
            default_desc = (
                f"defaults to \033[32m{a.default}\033[0m"
                if a.default_desc is None
                else a.default_desc
            )
            default = f" \033[33mOptional\033[0m, {default_desc}."

        return f"{os.linesep}{indent}{name}{separator}{a.desc}.{default}"

    @classmethod
    def _user_facing_error(cls, msg: str, *, exit_code: int = 1):
        print(cls._dedent(msg), file=sys.stderr)
        sys.exit(exit_code)

    @staticmethod
    def _dedent(text: str) -> str:
        return textwrap.dedent(text).strip()
