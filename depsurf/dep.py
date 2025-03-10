from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .diff import (
    BaseChange,
    diff_config,
    diff_enum,
    diff_func,
    diff_nop,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
)
from .funcs import FuncGroup
from .issues import IssueEnum
from .paths import REPORT_PATH
from .utils import OrderedEnum
from .version import Version


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

    @classmethod
    def from_dict(cls, data: Dict) -> "Dep":
        return cls(DepKind(data["kind"]), data["name"])

    @property
    def report_path(self) -> Path:
        return REPORT_PATH / self.kind / f"{self.name}.json"


@dataclass
class DepStatus:
    version: Version
    t: Optional[Dict]
    func_group: Optional[FuncGroup] = None

    @property
    def issues(self) -> List[IssueEnum]:
        if not self.exists:
            return [IssueEnum.ABSENT]

        if self.func_group:
            return self.func_group.issues

        return []

    @property
    def exists(self) -> bool:
        return self.t is not None

    @classmethod
    def from_dict(cls, data: Dict) -> "DepStatus":
        return cls(
            version=Version(**data["version"]),
            t=data["t"],
            func_group=FuncGroup.from_dict(data["func_group"])
            if data["func_group"]
            else None,
        )


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

    @property
    def is_both_absent(self) -> bool:
        return self.t1 is None and self.t2 is None

    @property
    def is_changed(self) -> bool:
        return bool(self.changes)

    @property
    def is_unchanged(self) -> bool:
        return self.t1 is not None and self.t2 is not None and not self.changes

    @classmethod
    def from_dict(cls, data: Dict) -> "DepDelta":
        return cls(
            v1=Version(**data["v1"]),
            v2=Version(**data["v2"]),
            t1=data["t1"],
            t2=data["t2"],
            changes=[BaseChange.from_dict(change) for change in data["changes"]],
        )
