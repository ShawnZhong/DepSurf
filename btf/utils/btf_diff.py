from enum import Enum
from dataclasses import dataclass


def diff_dict(old, new):
    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    common = {k: (old[k], new[k]) for k in old.keys() if k in new}
    return added, removed, common


@dataclass(frozen=True)
class DiffResult:
    added: set
    removed: set
    common: set
    changed: dict
    reasons: dict[str, int]


def print_as_list(name, s):
    l = list(s)
    print(f"{name} ({len(l)}): {l}")


def check_diff_impl(dict1, dict2, kind, diff_fn, all_reasons):
    # print_as_list(f"Old {kind}", dict1.keys())
    # print_as_list(f"New {kind}", dict2.keys())

    added, removed, common = diff_dict(dict1, dict2)
    # print_as_list(f"Common {kind}", common)
    print_as_list(f"Added {kind}", added)
    print_as_list(f"Removed {kind}", removed)

    changed = {
        name: diff_fn(old, new) for name, (old, new) in common.items() if old != new
    }
    print_as_list(f"Changed {kind}", changed.keys())

    reasons = {r.value: 0 for r in all_reasons}
    for changes in changed.values():
        for reason, detail in changes:
            reasons[reason.value] += 1
    print_as_list(f"Reasons {kind}", reasons.items())

    for name, changes in changed.items():
        print(name)
        for reason, detail in changes:
            print(f"\t{reason.value}")
            for line in detail:
                for l in line.split("\n"):
                    print(f"\t\t{l}")

    return DiffResult(added, removed, common, changed, reasons)
