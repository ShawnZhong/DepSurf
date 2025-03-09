from typing import List

from depsurf.btf import Kind

from .change import (
    BaseChange,
    FuncReturn,
    ParamAdd,
    ParamRemove,
    ParamReorder,
    ParamType,
)
from .diff_common import diff_dict


def diff_func(old, new) -> List[BaseChange]:
    assert old["kind"] == Kind.FUNC
    assert new["kind"] == Kind.FUNC

    result = []

    old_params = {p["name"]: p for p in old["type"]["params"]}
    new_params = {p["name"]: p for p in new["type"]["params"]}

    added, removed, common = diff_dict(old_params, new_params)

    # params added
    for name, value in added.items():
        result.append(ParamAdd(**value))

    # params removed
    for name, value in removed.items():
        result.append(ParamRemove(**value))

    # params reordered
    old_idx = {n: i for i, n in enumerate(old_params) if n in common}
    new_idx = {n: i for i, n in enumerate(new_params) if n in common}
    if old_idx != new_idx:
        result.append(ParamReorder(old_params, new_params))

    # params changed type
    changed_types = [
        (name, old_value["type"], new_value["type"])
        for name, (old_value, new_value) in common.items()
        if old_value["type"] != new_value["type"]
    ]
    for name, old_value, new_value in changed_types:
        result.append(ParamType(name, old_value, new_value))

    # changed return value
    old_ret = old["type"]["ret_type"]
    new_ret = new["type"]["ret_type"]
    if old_ret != new_ret:
        result.append(FuncReturn(old_ret, new_ret))

    return result
