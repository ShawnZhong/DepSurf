from dataclasses import dataclass


def diff_dict(old, new):
    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    common = {k: (old[k], new[k]) for k in old.keys() if k in new}
    return added, removed, common


def print_as_list(name, s):
    l = list(s)
    print(f"{name} ({len(l)}): {l}")


@dataclass(frozen=True)
class DiffSummary:
    added: set
    removed: set
    common: set
    changed: dict
    reasons: dict[str, int]


def check_diff_impl(dict1, dict2, kind, diff_fn, reason_enum):
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

    reasons = {r.value: 0 for r in reason_enum}
    for changes in changed.values():
        for reason in changes.reasons():
            reasons[reason.value] += 1
    print_as_list(f"Reasons {kind}", reasons.items())

    for name, changes in changed.items():
        print(name)
        changes.print(1)

    return DiffSummary(added, removed, common, changed, reasons)


class DiffChanges:
    def __init__(self):
        self.changes = []

    def add(self, reason, detail):
        assert isinstance(reason, str)
        assert isinstance(detail, list)
        for l in detail:
            assert isinstance(l, str)
        self.changes.append((reason, detail))

    def reasons(self):
        return [reason for reason, _ in self.changes]

    def repr(self, num_tabs=0):
        indent = "\t" * num_tabs
        result = ""
        for reason, detail in self.changes:
            result += f"{indent}{reason.value}\n"
            for line in detail:
                for l in line.split("\n"):
                    result += f"{indent}\t{l}\n"
        return result

    def print(self, num_tabs=0):
        print(self.repr(num_tabs), end="")

    def __repr__(self):
        return self.repr()

    def __iter__(self):
        return iter(self.changes)
