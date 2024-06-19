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
from depsurf.version import Version
from depsurf.issues import IssueList
from depsurf.utils import OrderedEnum
from depsurf.funcs import CollisionType, FuncGroup, InlineType
from depsurf.linux import FuncSymbolGroup


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
    CGROUP = "cgroup"

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
            "raw_tracepoint": DepKind.TRACEPOINT,
            "tracepoint": DepKind.TRACEPOINT,
            "lsm": DepKind.LSM,
            "uprobe": DepKind.UPROBE,
            "uretprobe": DepKind.UPROBE,
            "usdt": DepKind.USDT,
            "perf_event": DepKind.PERF_EVENT,
            "cgroup_skb": DepKind.CGROUP,
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
    version: Version
    exists: bool = True
    func_group: Optional[FuncGroup] = None
    sym_group: Optional[FuncSymbolGroup] = None

    @property
    def issues(self) -> IssueList:
        result = IssueList()
        if not self.exists:
            result.append(IssueEnum.ABSENT)

        if self.func_group:
            # collision
            collision = self.func_group.get_collision_type()
            if collision == CollisionType.INCLUDE_DUP:
                result.append(IssueEnum.DUPLICATE)
            elif collision in (
                CollisionType.STATIC_STATIC,
                CollisionType.STATIC_GLOBAL,
            ):
                result.append(IssueEnum.COLLISSION)

            # inline
            inline = self.func_group.get_inline_type(
                in_symtab=self.sym_group is not None
            )
            if inline == InlineType.FULL:
                result.append(IssueEnum.FULL_INLINE)
            elif inline == InlineType.PARTIAL:
                result.append(IssueEnum.PARTIAL_INLINE)

        # rename
        if self.sym_group and self.sym_group.has_suffix:
            result.append(IssueEnum.RENAME)

        return result

    def __str__(self):
        return " ".join([e.get_symbol(emoji=True) for e in self.issues])

    @property
    def is_ok(self) -> bool:
        return len(self.issues) == 0

    def print(self, file=None, nindent=0):
        indent = "\t" * nindent
        print(f"{indent}In {self.version}: {self.issues}", file=file)

        if self.func_group:
            self.func_group.print_funcs(file=file, nindent=nindent + 1)

        if self.sym_group:
            self.sym_group.print(file=file, nindent=nindent + 1)


@dataclass
class DepDelta:
    v1: Version
    v2: Version
    in_v1: bool = True
    in_v2: bool = True
    changes: List[BaseChange] = dataclasses.field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def status_str(self) -> str:
        if not self.in_v1 and not self.in_v2:
            return "Both absent"
        if not self.in_v1:
            return f"Added"
        if not self.in_v2:
            return f"Removed"
        if self.has_changes:
            return "Changed"
        return "No changes"

    def print(self, file=None, nindent=0):
        indent = "\t" * nindent

        print(
            f"{indent}From {self.v1} to {self.v2}: {self.status_str}",
            file=file,
        )

        for change in self.changes:
            change.print(file=file, nindent=nindent + 1)
