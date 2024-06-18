import dataclasses
from dataclasses import dataclass
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
from depsurf.issues import IssueList
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


@dataclass
class DepStatus:
    exists: bool = True
    group: Optional[FuncGroup] = None
    inline: Optional[InlineType] = None
    collision: Optional[CollisionType] = None
    suffix: bool = False

    @property
    def issues(self) -> IssueList:
        result = IssueList()
        if not self.exists:
            result.append(IssueEnum.ABSENT)

        if self.collision in (
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

        return result

    def __str__(self):
        return " ".join([e.get_symbol(emoji=True) for e in self.issues])

    @property
    def text(self):
        return "".join([e.get_symbol() for e in self.issues])

    @property
    def is_ok(self) -> bool:
        return len(self.issues) == 0

    def print(self, file=None, nindent=0):
        indent = "\t" * nindent
        print(f"{indent}Issues: {self.issues}", file=file)

        if self.group:
            self.group.print_funcs(file=file, nindent=nindent + 1)


@dataclass
class DepDelta:
    in_v1: bool = True
    in_v2: bool = True
    changes: List[BaseChange] = dataclasses.field(default_factory=list)

    @property
    def issues(self) -> IssueList:
        if not self.in_v1 and not self.in_v2:
            return IssueList(IssueEnum.BOTH_ABSENT)
        if not self.in_v1 and self.in_v2:
            return IssueList(IssueEnum.ADD)
        if self.in_v1 and not self.in_v2:
            return IssueList(IssueEnum.REMOVE)
        if self.changes:
            return IssueList(*[e.enum for e in self.changes])
        return IssueList()

    def __bool__(self):
        return bool(self.changes)

    @property
    def text(self):
        for issue in [IssueEnum.ADD, IssueEnum.REMOVE, IssueEnum.NO_CHANGE]:
            if issue in self.issues:
                assert len(self.issues) == 1
                return ""
        num = len(self.changes)
        if num == 0:
            return ""
        return str(num)

    def print(self, file=None, nindent=0):
        if not self:
            return
        indent = "\t" * nindent
        for change in self.changes:
            print(f"{indent}{change}", file=file)
