from dataclasses import dataclass
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
from depsurf.version import Version


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

    def __repr__(self):
        return self.value


@dataclass(frozen=True, order=True)
class Dep:
    kind: DepKind
    name: str


NUM_EMOJI = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]


@dataclass
class DepDelta:
    changes: Optional[List[BaseChange]] = None

    def __str__(self):
        if self.changes is None:
            return ""
        num_changes = len(self.changes)
        if num_changes == 0:
            return "."
        return "".join([NUM_EMOJI[int(digit)] for digit in str(num_changes)])

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
                CollisionType.INCLUDE: f"🟣{self.collision}",
                CollisionType.STATIC: f"🟣{self.collision}",
                CollisionType.MIXED: f"🟣{self.collision}",
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
