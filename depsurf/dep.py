import dataclasses
from dataclasses import dataclass
from collections import defaultdict
from enum import StrEnum
from typing import Callable, Dict, List, Optional

from depsurf.diff import (
    IssueEnum,
    BaseChange,
    diff_enum,
    diff_func,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
    diff_nop,
    diff_config,
)
from depsurf.utils import OrderedEnum
from depsurf.funcs import CollisionType, FuncGroup, InlineType


class DepKind(OrderedEnum, StrEnum):
    FUNC = "Function"
    STRUCT = "Struct"
    FIELD = "Field"
    TRACEPOINT = "Tracepoint"
    LSM = "LSM Hook"
    SYSCALL = "Syscall"

    UNION = "Union"
    ENUM = "Enum"

    UPROBE = "uprobe"
    USDT = "USDT"
    PERF_EVENT = "Perf Event"

    CONFIG = "Config"

    @staticmethod
    def from_hook_name(name: str):
        if name.startswith("tracepoint/syscalls/"):
            return DepKind.SYSCALL

        prefix = name.split("/")[0]
        return {
            "kprobe": DepKind.FUNC,
            "kretprobe": DepKind.FUNC,
            "fentry": DepKind.FUNC,
            "fexit": DepKind.FUNC,
            "tp_btf": DepKind.TRACEPOINT,
            "raw_tp": DepKind.TRACEPOINT,
            "tracepoint": DepKind.TRACEPOINT,
            "lsm": DepKind.LSM,
            "uprobe": DepKind.UPROBE,
            "uretprobe": DepKind.UPROBE,
            "usdt": DepKind.USDT,
            "perf_event": DepKind.PERF_EVENT,
        }[prefix]

    @property
    def differ(self) -> Callable[[Dict, Dict], List[BaseChange]]:
        return {
            DepKind.STRUCT: diff_struct,
            DepKind.FIELD: diff_struct_field,
            DepKind.FUNC: diff_func,
            DepKind.TRACEPOINT: diff_tracepoint,
            DepKind.LSM: diff_func,
            DepKind.UNION: diff_struct,
            DepKind.ENUM: diff_enum,
            DepKind.SYSCALL: diff_nop,
            DepKind.CONFIG: diff_config,
        }[self]

    def __call__(self, name):
        return Dep(self, name)

    def __repr__(self):
        return self.value


@dataclass(frozen=True, order=True)
class Dep:
    kind: DepKind
    name: str

    def __str__(self):
        return f"{self.kind.value}({self.name})"


class BaseDepCell:
    @property
    def background_color(self):
        from matplotlib import colors

        return colors.to_rgb(self.background_color_name)

    @property
    def background_color_name(self):
        raise NotImplementedError

    @property
    def text(self):
        raise NotImplementedError

    @property
    def text_color(self):
        return "white"


@dataclass
class DepDelta(BaseDepCell):
    in_v1: bool = True
    in_v2: bool = True
    changes: List[BaseChange] = dataclasses.field(default_factory=list)

    @property
    def enum(self) -> IssueEnum:
        if not self.in_v1 and not self.in_v2:
            return IssueEnum.BOTH_ABSENT
        if not self.in_v1 and self.in_v2:
            return IssueEnum.ADD
        if self.in_v1 and not self.in_v2:
            return IssueEnum.REMOVE
        if self.changes:
            return IssueEnum.CHANGE
        return IssueEnum.NO_CHANGE

    def __str__(self):
        if self.enum != IssueEnum.CHANGE:
            return self.enum.get_symbol(emoji=True)

        change_enums: Dict[IssueEnum, int] = defaultdict(int)
        for change in self.changes:
            change_enums[change.enum] += 1

        result = ""
        for k, v in change_enums.items():
            if v == 1:
                result += f"{k.get_symbol()} "
            else:
                result += f"{k.get_symbol()}⨉{v} "
        return result

    def __bool__(self):
        return bool(self.changes)

    @property
    def background_color_name(self):
        return self.enum.color

    @property
    def text(self):
        if self.enum == IssueEnum.CHANGE:
            return str(len(self.changes))
        return self.enum.get_symbol()

    @property
    def text_color(self):
        return "black" if self.enum == IssueEnum.NO_CHANGE else "white"

    def print(self, file=None, nindent=0):
        if not self:
            return
        indent = "\t" * nindent
        print(f"{indent}{len(self.changes)} changes", file=file)
        indent = "\t" * (nindent + 1)
        for change in self.changes:
            print(f"{indent}{change}", file=file)


@dataclass
class DepStatus(BaseDepCell):
    exists: bool = True
    group: Optional[FuncGroup] = None
    inline: Optional[InlineType] = None
    collision: Optional[CollisionType] = None
    suffix: bool = False

    @property
    def enums(self) -> List[IssueEnum]:
        result = []
        if not self.exists:
            result.append(IssueEnum.ABSENT)

        if self.collision == CollisionType.UNIQUE_STATIC:
            result.append(IssueEnum.STATIC)
        elif self.collision in (
            CollisionType.INCLUDE_DUP,
            CollisionType.STATIC_STATIC,
            CollisionType.STATIC_GLOBAL,
        ):
            result.append(IssueEnum.DUPLICATE)

        if self.inline == InlineType.FULL:
            result.append(IssueEnum.FULL_INLINE)
        elif self.inline == InlineType.PARTIAL:
            result.append(IssueEnum.PARTIAL_INLINE)

        if self.suffix:
            result.append(IssueEnum.RENAME)

        if not result:
            result.append(IssueEnum.OK)

        return result

    def __str__(self):
        return " ".join([e.get_symbol(emoji=True) for e in self.enums])

    @property
    def text(self):
        return "".join([e.get_symbol() for e in self.enums])

    @property
    def background_color_name(self):
        if self.enums == [IssueEnum.STATIC]:
            return IssueEnum.OK.color
        for enum in list(IssueEnum)[::-1]:
            if enum in self.enums:
                return enum.color

    def __bool__(self):
        return self.enums == [IssueEnum.OK]

    def print(self, file=None, nindent=0):
        if not self:
            return
        indent = "\t" * nindent
        print(indent + " ".join([e.name for e in self.enums]), file=file)

        if self.group:
            self.group.print_funcs(file=file, nindent=nindent + 1)
