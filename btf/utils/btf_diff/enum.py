from enum import Enum
from ..btf import Kind
from .impl import diff_dict, DiffChanges


class EnumChange(str, Enum):
    ADD = "Elem added"
    REMOVE = "Elem removed"
    VALUE = "Value changed"

    @property
    def consequence(self):
        from . import Consequence

        return {
            EnumChange.ADD: Consequence.COMPILER,
            EnumChange.REMOVE: Consequence.COMPILER,
            EnumChange.VALUE: Consequence.CORE,
        }[self]


def diff_enum(old, new):
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
            [f"{name:40}: {value['val']}" for name, value in added.items()],
        )

    # removed value
    if removed:
        result.add(
            EnumChange.REMOVE,
            [f"{name:40}: {value['val']}" for name, value in removed.items()],
        )

    # values changed
    changed_values = {
        name: (old_value["val"], new_value["val"])
        for name, (old_value, new_value) in common.items()
        if old_value["val"] != new_value["val"]
    }
    if changed_values:
        result.add(
            EnumChange.VALUE,
            [
                f"{name:40}: {old_val} -> {new_val}"
                for name, (old_val, new_val) in changed_values.items()
            ],
        )

    assert result, f"\n{old}\n{new}"
    return result
