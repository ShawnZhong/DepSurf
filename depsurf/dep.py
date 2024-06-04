import dataclasses
from dataclasses import dataclass
from collections import defaultdict
from enum import StrEnum, Enum, auto
from typing import Callable, Dict, List, Optional

from depsurf.diff import (
    BaseChange,
    diff_enum,
    diff_func,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
    diff_syscall,
)
from depsurf.funcs import CollisionType, FuncGroup, InlineType


class DepKind(StrEnum):
    STRUCT = "Struct"
    FIELD = "Field"
    FUNC = "Function"
    TRACEPOINT = "Tracepoint"
    LSM = "LSM"
    UNION = "Union"
    ENUM = "Enum"
    SYSCALL = "Syscall"

    # other kinds of hooks supported by BPF
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
            DepKind.FIELD: diff_struct_field,
            DepKind.FUNC: diff_func,
            DepKind.TRACEPOINT: diff_tracepoint,
            DepKind.LSM: diff_func,
            DepKind.UNION: diff_struct,
            DepKind.ENUM: diff_enum,
            DepKind.SYSCALL: diff_syscall,
        }[self]

    def __call__(self, name):
        return Dep(self, name)

    def __repr__(self):
        return self.value


@dataclass(frozen=True, order=True)
class Dep:
    kind: DepKind
    name: str


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


class DepDeltaEnum(Enum):
    ADD = auto()
    REMOVE = auto()
    CHANGE = auto()
    NO_CHANGE = auto()
    NOT_EXIST = auto()

    @property
    def color(self):
        return {
            DepDeltaEnum.ADD: "tab:blue",
            DepDeltaEnum.REMOVE: "tab:red",
            DepDeltaEnum.CHANGE: "tab:orange",
            DepDeltaEnum.NO_CHANGE: "whitesmoke",
            DepDeltaEnum.NOT_EXIST: "white",
        }[self]

    @property
    def name(self):
        return {
            DepDeltaEnum.ADD: "Add",
            DepDeltaEnum.REMOVE: "Remove",
            DepDeltaEnum.CHANGE: "Change",
            DepDeltaEnum.NO_CHANGE: "No Change",
        }[self]

    @property
    def symbol(self):
        return {
            DepDeltaEnum.ADD: "+",
            DepDeltaEnum.REMOVE: "−",
            DepDeltaEnum.NO_CHANGE: "·",
            DepDeltaEnum.CHANGE: "42",
            DepDeltaEnum.NOT_EXIST: "",
        }[self]

    @property
    def emoji(self):
        return {
            DepDeltaEnum.ADD: "🔺",
            DepDeltaEnum.REMOVE: "🔻",
            DepDeltaEnum.NO_CHANGE: "·",
            DepDeltaEnum.NOT_EXIST: "",
        }[self]

    @property
    def text_color(self):
        return "black" if self == DepDeltaEnum.NO_CHANGE else "white"


@dataclass
class DepDelta(BaseDepCell):
    in_v1: bool = True
    in_v2: bool = True
    changes: Optional[List[BaseChange]] = None

    @property
    def enum(self):
        if not self.in_v1 and not self.in_v2:
            return DepDeltaEnum.NOT_EXIST
        if not self.in_v1 and self.in_v2:
            return DepDeltaEnum.ADD
        if self.in_v1 and not self.in_v2:
            return DepDeltaEnum.REMOVE
        if self.changes:
            return DepDeltaEnum.CHANGE
        return DepDeltaEnum.NO_CHANGE

    def __str__(self):
        if self.enum != DepDeltaEnum.CHANGE:
            return self.enum.emoji

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

    @property
    def background_color_name(self):
        return self.enum.color

    @property
    def text(self):
        if self.enum == DepDeltaEnum.CHANGE:
            return str(len(self.changes))
        return self.enum.symbol

    @property
    def text_color(self):
        return self.enum.text_color

    def print(self, file=None, nindent=0):
        if not self:
            return
        indent = "\t" * nindent
        print(f"{indent}{len(self.changes)} changes", file=file)
        indent = "\t" * (nindent + 1)
        for change in self.changes:
            print(f"{indent}{change}", file=file)


class DepStatusEnum(Enum):
    OK = auto()
    ABSENT = auto()
    STATIC = auto()
    PARTIAL_INLINE = auto()
    FULL_INLINE = auto()
    RENAME = auto()
    DUPLICATE = auto()

    @property
    def color(self):
        return {
            DepStatusEnum.OK: "tab:green",
            DepStatusEnum.ABSENT: "tab:red",
            DepStatusEnum.DUPLICATE: "black",
            DepStatusEnum.RENAME: "blue",
            DepStatusEnum.PARTIAL_INLINE: "tab:blue",
            DepStatusEnum.FULL_INLINE: "darkblue",
            DepStatusEnum.STATIC: "gray",
        }[self]

    @property
    def emoji(self):
        return {
            DepStatusEnum.OK: "✅",
            DepStatusEnum.ABSENT: "❌",
            DepStatusEnum.DUPLICATE: "🟣D",
            DepStatusEnum.RENAME: "🔵R",
            DepStatusEnum.PARTIAL_INLINE: "🟡P",
            DepStatusEnum.FULL_INLINE: "🟠F",
            DepStatusEnum.STATIC: "🟣S",
        }[self]

    @property
    def symbol(self):
        return {
            DepStatusEnum.OK: "",
            DepStatusEnum.ABSENT: "✗",
            DepStatusEnum.DUPLICATE: "D",
            DepStatusEnum.RENAME: "R",
            DepStatusEnum.PARTIAL_INLINE: "P",
            DepStatusEnum.FULL_INLINE: "F",
            DepStatusEnum.STATIC: "S",
        }[self]

    @property
    def name(self):
        return {
            DepStatusEnum.OK: "OK",
            DepStatusEnum.ABSENT: "Absent",
            DepStatusEnum.DUPLICATE: "Duplicate",
            DepStatusEnum.RENAME: "Rename",
            DepStatusEnum.PARTIAL_INLINE: "Partial Inline",
            DepStatusEnum.FULL_INLINE: "Full Inline",
            DepStatusEnum.STATIC: "Static",
        }[self]


@dataclass
class DepStatus(BaseDepCell):
    exists: bool = True
    group: FuncGroup = None
    inline: InlineType = None
    collision: CollisionType = None
    suffix: bool = False

    @property
    def enums(self) -> List[DepStatusEnum]:
        result = []
        if not self.exists:
            result.append(DepStatusEnum.ABSENT)

        if self.collision == CollisionType.UNIQUE_STATIC:
            result.append(DepStatusEnum.STATIC)
        elif self.collision in (
            CollisionType.INCLUDE_DUP,
            CollisionType.STATIC_STATIC,
            CollisionType.STATIC_GLOBAL,
        ):
            result.append(DepStatusEnum.DUPLICATE)

        if self.inline == InlineType.FULL:
            result.append(DepStatusEnum.FULL_INLINE)
        elif self.inline == InlineType.PARTIAL:
            result.append(DepStatusEnum.PARTIAL_INLINE)

        if self.suffix:
            result.append(DepStatusEnum.RENAME)

        if not result:
            result.append(DepStatusEnum.OK)

        return result

    def __str__(self):
        return " ".join([e.emoji for e in self.enums])

    @property
    def text(self):
        return "".join([e.symbol for e in self.enums])

    @property
    def background_color_name(self):
        if self.enums == [DepStatusEnum.STATIC]:
            return DepStatusEnum.OK.color
        for enum in list(DepStatusEnum)[::-1]:
            if enum in self.enums:
                return enum.color

    def __bool__(self):
        return self.enums == [DepStatusEnum.OK]

    def print(self, file=None, nindent=0):
        if not self:
            return
        indent = "\t" * nindent
        print(indent + " ".join([e.name for e in self.enums]), file=file)

        if self.group:
            self.group.print_funcs(file=file, nindent=nindent + 1)
