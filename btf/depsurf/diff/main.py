from dataclasses import dataclass
from typing import Callable, Dict

from depsurf.btf import Kind

from .changes import DiffChanges
from .enum import EnumChange, diff_enum
from .func import FuncChange, diff_func
from .struct import StructChange, diff_struct
from .utils import diff_dict


def get_diff_fn(kind) -> Callable[[dict, dict], DiffChanges]:
    return {
        Kind.STRUCT: diff_struct,
        Kind.UNION: diff_struct,
        Kind.FUNC: diff_func,
        Kind.ENUM: diff_enum,
    }[kind]


def get_reason_enum(kind):
    return {
        Kind.STRUCT: StructChange,
        Kind.UNION: StructChange,
        Kind.FUNC: FuncChange,
        Kind.ENUM: EnumChange,
    }[kind]


@dataclass(frozen=True)
class DiffSummary:
    added: set
    removed: set
    common: set
    changed: dict[str, DiffChanges]
    reasons: dict[str, int]


def print_as_list(name, s):
    l = list(s)
    print(f"{name} ({len(l)}): {l}")


def check_diff(dict1, dict2) -> DiffSummary:
    kind1 = next(iter(dict1.values()))["kind"]
    kind2 = next(iter(dict2.values()))["kind"]
    assert kind1 == kind2
    kind = Kind(kind1)
    diff_fn = get_diff_fn(kind)
    reason_enum = get_reason_enum(kind)
    return check_diff_impl(dict1, dict2, kind, diff_fn, reason_enum)


def check_diff_impl(dict1, dict2, kind, diff_fn, reason_enum) -> DiffSummary:
    # print_as_list(f"Old {kind}", dict1.keys())
    # print_as_list(f"New {kind}", dict2.keys())

    added, removed, common = diff_dict(dict1, dict2)
    # print_as_list(f"Common {kind}", common)
    print_as_list(f"Added {kind}", added)
    print_as_list(f"Removed {kind}", removed)

    changed: Dict[str, DiffChanges] = {
        name: diff_fn(old, new, assert_diff=False)  # TODO: assert_diff
        for name, (old, new) in common.items()
        if old != new
    }
    print_as_list(f"Changed {kind}", changed.keys())

    reasons = {r: 0 for r in reason_enum}
    for changes in changed.values():
        for reason in changes.reasons:
            reasons[reason] += 1
    print_as_list(f"Reasons {kind}", reasons.items())

    for name, changes in changed.items():
        print(name)
        changes.print(1)

    return DiffSummary(added, removed, common, changed, reasons)
