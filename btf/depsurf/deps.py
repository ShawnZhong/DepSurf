from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Dict

from depsurf.cause import cause_sort_key
from depsurf.diff import (
    DiffChanges,
    compare_eq,
    diff_dict,
    diff_enum,
    diff_func,
    diff_struct,
)
from depsurf.linux import LinuxImage, TracepointInfo


def diff_tracepoint(old: TracepointInfo, new: TracepointInfo, assert_diff=False):
    result_struct = diff_struct(old.struct, new.struct, assert_diff)
    result_func = diff_func(old.func, new.func, assert_diff)
    return result_struct + result_func


@dataclass(frozen=True)
class ImageDiffResult:
    old: dict
    new: dict
    added: set
    removed: set
    common: set
    changed: dict[str, DiffChanges]
    reasons: dict[str, int]

    def print(self):
        print(f"Added ({len(self.added)}): {list(self.added)}")
        print(f"Removed ({len(self.removed)}): {list(self.removed)}")
        print(f"Changed ({len(self.changed)}): {list(self.changed)}")
        print(f"Reasons: {[(str(r), v) for (r, v) in self.reasons.items() if v != 0]}")

        for name, changes in self.changed.items():
            print(name)
            # print(f"\tOld: {dict1[name]}")
            # print(f"\tNew: {dict2[name]}")
            changes.print(1)


class DepKind(StrEnum):
    STRUCT = "Struct"
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
    def from_hook_name(name):
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

    def getter(self, img: LinuxImage):
        return {
            DepKind.STRUCT: img.btf.structs,
            DepKind.FUNC: img.btf.funcs,
            DepKind.TRACEPOINT: img.tracepoints.data,
            DepKind.LSM: img.lsm_hooks,
            DepKind.UNION: img.btf.unions,
            DepKind.ENUM: img.btf.enums,
        }[self]

    def is_available(self, img: LinuxImage, name: str):
        return self.getter(img)[name] is not None

    @property
    def differ(self):
        return {
            DepKind.STRUCT: diff_struct,
            DepKind.FUNC: diff_func,
            DepKind.TRACEPOINT: diff_tracepoint,
            DepKind.LSM: diff_func,
            DepKind.UNION: diff_struct,
            DepKind.ENUM: diff_enum,
        }[self]

    def is_changed(self, img1: LinuxImage, img2: LinuxImage, name: str):
        t1 = self.getter(img1)(name)
        t2 = self.getter(img2)(name)
        if t1 is None or t2 is None:
            return None
        return bool(self.differ()(t1, t2))

    def diff_img(self, img1: LinuxImage, img2: LinuxImage) -> ImageDiffResult:
        dict1 = self.getter(img1)
        dict2 = self.getter(img2)
        added, removed, common = diff_dict(dict1, dict2)

        changed: Dict[str, DiffChanges] = {
            name: self.differ(old, new, assert_diff=False)  # TODO: assert_diff
            for name, (old, new) in common.items()
            if not compare_eq(old, new)
        }

        reasons = defaultdict(int)
        for changes in changed.values():
            for reason in changes.reasons:
                reasons[reason] += 1

        reasons = sorted(reasons.items(), key=lambda x: cause_sort_key(x[0]))

        return ImageDiffResult(
            old=dict1,
            new=dict2,
            added=added,
            removed=removed,
            common=common,
            changed=changed,
            reasons=dict(reasons),
        )

    def __repr__(self):
        return f"'{self.value}'"
