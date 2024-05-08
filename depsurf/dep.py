from dataclasses import dataclass
from collections import defaultdict
from enum import StrEnum
from typing import Callable, Dict, List, Optional

from depsurf.diff import (
    BaseChange,
    diff_enum,
    diff_func,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
)
from depsurf.dwarf import CollisionType, FuncGroup, InlineType


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
    def differ(self) -> Callable[[Dict, Dict], List[BaseChange]]:
        return {
            DepKind.STRUCT: diff_struct,
            DepKind.STRUCT_FIELD: diff_struct_field,
            DepKind.FUNC: diff_func,
            DepKind.TRACEPOINT: diff_tracepoint,
            DepKind.LSM: diff_func,
            DepKind.UNION: diff_struct,
            DepKind.ENUM: diff_enum,
        }[self]

    def __call__(self, name):
        return Dep(self, name)

    def __repr__(self):
        return self.value


@dataclass(frozen=True, order=True)
class Dep:
    kind: DepKind
    name: str


@dataclass
class DepDelta:
    in_v1: bool = True
    in_v2: bool = True
    changes: Optional[List[BaseChange]] = None

    def __str__(self):
        if not self.in_v1 and not self.in_v2:
            return ""
        if not self.in_v1 and self.in_v2:
            return "🔺"
        if self.in_v1 and not self.in_v2:
            return "🔻"
        assert self.changes is not None, repr(self)
        num_changes = len(self.changes)
        if num_changes == 0:
            return "."
        change_enums = defaultdict(int)
        for change in self.changes:
            change_enums[change.enum] += 1

        result = ""
        for k, v in change_enums.items():
            if v == 1:
                result += f"{k.short} "
            else:
                result += f"{k.short}⨉{v} "
        return result

    def __bool__(self):
        return bool(self.changes)

    def print(self, file=None, nindent=0):
        if not self:
            return
        indent = "\t" * nindent
        print(f"{indent}{len(self.changes)} changes", file=file)
        indent = "\t" * (nindent + 1)
        for change in self.changes:
            print(f"{indent}{change}", file=file)


@dataclass
class DepStatus:
    exists: bool
    group: FuncGroup = None
    inline: InlineType = None
    collision: CollisionType = None
    suffix: bool = False

    @property
    def issues(self):
        results = {}
        if not self.exists:
            results["Not exist"] = "❌"
        if self.inline:
            s = {
                InlineType.NOT: None,
                InlineType.FULL: f"🟠F",
                InlineType.PARTIAL: f"🟡P",
            }[self.inline]
            if s is not None:
                results[self.inline] = s
        if self.suffix:
            results["Renamed"] = "🔵R"
        if self.collision:
            s = {
                CollisionType.UNIQUE_GLOBAL: None,
                CollisionType.UNIQUE_STATIC: "🟣S",
                CollisionType.INCLUDE: f"🟣D",
                CollisionType.STATIC: f"🟣SS",
                CollisionType.MIXED: f"🟣SG",
            }[self.collision]
            if s is not None:
                results[self.collision] = s
        return results

    def __str__(self):
        issues = self.issues.values()
        return " ".join(issues) if issues else "✅"

    def __bool__(self):
        return bool(self.issues)

    def print(self, file=None, nindent=0):
        issues = self.issues
        if not issues:
            return
        indent = "\t" * nindent
        print(indent + " ".join(issues.keys()), file=file)

        if self.group:
            self.group.print_funcs(file=file, nindent=nindent + 1)
