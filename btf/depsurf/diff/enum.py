from depsurf.btf import Kind
from .utils import diff_dict
from .changes import DiffChanges
from depsurf.cause import EnumChange


def diff_enum(old, new, assert_diff=False):
    assert old["kind"] == Kind.ENUM
    assert new["kind"] == Kind.ENUM

    result = DiffChanges()

    old_values = {v["name"]: v for v in old["values"]}
    new_values = {v["name"]: v for v in new["values"]}

    added, removed, common = diff_dict(old_values, new_values)

    # added value
    if added:
        result.add(
            EnumChange.ADD,
            [(name, value["val"]) for name, value in added.items()],
        )

    # removed value
    if removed:
        result.add(
            EnumChange.REMOVE,
            [(name, value["val"]) for name, value in removed.items()],
        )

    # values changed
    changed_values = [
        (name, old_value["val"], new_value["val"])
        for name, (old_value, new_value) in common.items()
        if old_value["val"] != new_value["val"]
    ]
    if changed_values:
        result.add(EnumChange.VALUE, changed_values)

    if assert_diff:
        assert result, f"\n{old}\n{new}"
    return result
