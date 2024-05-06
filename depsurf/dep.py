from dataclasses import dataclass
from enum import StrEnum
from typing import Callable, Dict, List

from depsurf.diff import (
    BaseCause,
    diff_enum,
    diff_func,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
)

from depsurf.dwarf import CollisionType, InlineType


class DepKind(StrEnum):
    STRUCT = "Struct"
    STRUCT_FIELD = "Field"
    FUNC = "Function"
    TRACEPOINT = "Tracepoint"
    LSM = "LSM"
    UNION = "Union"
    ENUM = "Enum"

    # other kinds of hooks supported by BPF
    SYSCALL = "Syscall"
    UPROBE = "uprobe"
    USDT = "USDT"
    PERF_EVENT = "Perf Event"

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
    def differ(self) -> Callable[[Dict, Dict], List[BaseCause]]:
        return {
            DepKind.STRUCT: diff_struct,
            DepKind.STRUCT_FIELD: diff_struct_field,
            DepKind.FUNC: diff_func,
            DepKind.TRACEPOINT: diff_tracepoint,
            DepKind.LSM: diff_func,
            DepKind.UNION: diff_struct,
            DepKind.ENUM: diff_enum,
        }[self]

    def __repr__(self):
        return self.value


@dataclass(frozen=True, order=True)
class Dep:
    kind: DepKind
    name: str


@dataclass
class DepStatus:
    exists: bool
    inline: InlineType = None
    collision: CollisionType = None
    suffix: bool = False

    def __str__(self):
        if not self.exists:
            return "❌"
        result = ""
        if self.collision:
            result += {
                CollisionType.UNIQUE_GLOBAL: "",
                CollisionType.UNIQUE_STATIC: "🟣 Static",
                CollisionType.INCLUDE: f"🟣 {self.collision}",
                CollisionType.STATIC: f"🟣 {self.collision}",
                CollisionType.MIXED: f"🟣 {self.collision}",
            }[self.collision]
        if self.inline:
            result += {
                InlineType.NOT: "",
                InlineType.FULL: f"🟠 {self.inline}",
                InlineType.PARTIAL: f"🟡 {self.inline}",
            }[self.inline]
        if self.suffix:
            result += f"🔵 Suffix"
        if not result:
            result = "✅"
        return result
