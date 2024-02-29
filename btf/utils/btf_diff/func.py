from enum import Enum
from ..btf import Kind
from .impl import diff_dict, DiffChanges


class FuncChange(str, Enum):
    ADD = "Param added"
    REMOVE = "Param removed"
    TYPE = "Param type changed"
    REORDER = "Param reordered"
    RETURN = "Return type changed"

    @property
    def consequence(self):
        from . import Consequence

        return {
            FuncChange.ADD: Consequence.SLIENT,
            FuncChange.REMOVE: Consequence.SLIENT,
            FuncChange.TYPE: Consequence.SLIENT,
            FuncChange.REORDER: Consequence.SLIENT,
            FuncChange.RETURN: Consequence.SLIENT,
        }[self]


def diff_func(old, new):
    assert old["kind"] == Kind.FUNC
    assert new["kind"] == Kind.FUNC

    result = DiffChanges()

    old_params = {p["name"]: p for p in old["type"]["params"]}
    new_params = {p["name"]: p for p in new["type"]["params"]}

    added, removed, common = diff_dict(old_params, new_params)

    # params added
    if added:
        result.add(
            FuncChange.ADD,
            [f"{name:20}: {value['type']}" for name, value in added.items()],
        )

    # params removed
    if removed:
        result.add(
            FuncChange.REMOVE,
            [f"{name:20}: {value['type']}" for name, value in removed.items()],
        )

    # params reordered
    old_idx = {n: i for i, n in enumerate(old_params) if n in common}
    new_idx = {n: i for i, n in enumerate(new_params) if n in common}
    if old_idx != new_idx:
        result.add(
            FuncChange.REORDER,
            [f"{'':20} {list(old_params)}\n{'':20} {list(new_params)}"],
        )

    # params changed type
    changed_types = {
        name: (old_value["type"], new_value["type"])
        for name, (old_value, new_value) in common.items()
        if old_value["type"] != new_value["type"]
    }
    if changed_types:
        result.add(
            FuncChange.TYPE,
            [
                f"{name:20}: {old_type}\n{'':20}->{new_type}"
                for name, (old_type, new_type) in changed_types.items()
            ],
        )

    # changed return value
    old_ret = old["type"]["ret_type"]
    new_ret = new["type"]["ret_type"]
    if old_ret != new_ret:
        result.add(
            FuncChange.RETURN,
            [f"{'':20}: {old_ret}\n{'':20}->{new_ret}"],
        )

    assert result, f"\n{old}\n{new}"
    return result
