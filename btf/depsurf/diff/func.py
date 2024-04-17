from depsurf.btf import Kind
from .utils import diff_dict
from .changes import DiffChanges
from depsurf.cause import FuncCause


def diff_func(old, new, assert_diff=False):
    assert old["kind"] == Kind.FUNC
    assert new["kind"] == Kind.FUNC

    result = DiffChanges()

    old_params = {p["name"]: p for p in old["type"]["params"]}
    new_params = {p["name"]: p for p in new["type"]["params"]}

    added, removed, common = diff_dict(old_params, new_params)

    # params added
    if added:
        result.add(
            FuncCause.PARAM_ADD,
            [(name, value["type"]) for name, value in added.items()],
        )

    # params removed
    if removed:
        result.add(
            FuncCause.PARAM_REMOVE,
            [(name, value["type"]) for name, value in removed.items()],
        )

    # params reordered
    old_idx = {n: i for i, n in enumerate(old_params) if n in common}
    new_idx = {n: i for i, n in enumerate(new_params) if n in common}
    if old_idx != new_idx:
        result.add(
            FuncCause.PARAM_REORDER,
            [(list(old_params), list(new_params))],
        )

    # params changed type
    changed_types = [
        (name, old_value["type"], new_value["type"])
        for name, (old_value, new_value) in common.items()
        if old_value["type"] != new_value["type"]
    ]
    if changed_types:
        result.add(FuncCause.PARAM_TYPE, changed_types)

    # changed return value
    old_ret = old["type"]["ret_type"]
    new_ret = new["type"]["ret_type"]
    if old_ret != new_ret:
        result.add(FuncCause.FUNC_RETURN, [(old_ret, new_ret)])

    if assert_diff:
        assert result, f"\n{old}\n{new}"

    return result
