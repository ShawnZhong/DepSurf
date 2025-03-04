import dataclasses
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Dict, List, Optional

from depsurf.diff import (
    BaseChange,
    diff_config,
    diff_enum,
    diff_func,
    diff_nop,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
)
from depsurf.funcs import FuncGroup
from depsurf.issues import IssueEnum
from depsurf.utils import OrderedEnum
from depsurf.version import Version


class DepKind(OrderedEnum, StrEnum):
    FUNC = "Function"
    STRUCT = "Struct"
    FIELD = "Field"
    TRACEPOINT = "Tracepoint"
    LSM = "LSM Hook"
    KFUNC = "kfunc"
    SYSCALL = "Syscall"

    UNION = "Union"
    ENUM = "Enum"

    UPROBE = "uprobe"
    USDT = "USDT"
    PERF_EVENT = "Perf Event"
    CGROUP = "cgroup"

    CONFIG = "Config"

    REGISTER = "Register"

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
            DepKind.KFUNC: diff_func,
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
        return f"{self.kind.value} {self.name}"


@dataclass
class DepStatus:
    version: Version
    exists: bool = True
    func_group: Optional[FuncGroup] = None

    @property
    def issues(self) -> List[IssueEnum]:
        if not self.exists:
            return [IssueEnum.ABSENT]

        if self.func_group:
            return self.func_group.issues

        return []


@dataclass
class DepDelta:
    v1: Version
    v2: Version
    t1: Optional[Dict]
    t2: Optional[Dict]
    changes: List[BaseChange]

    @property
    def is_added(self) -> bool:
        return self.t1 is None and self.t2 is not None

    @property
    def is_removed(self) -> bool:
        return self.t1 is not None and self.t2 is None
