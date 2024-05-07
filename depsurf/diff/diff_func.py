from dataclasses import dataclass
from typing import List

from depsurf.btf import Kind, get_btf_type_str

from .change import BaseChange, BaseChangeEnum, Consequence
from .utils import diff_dict


class FuncChangeEnum(BaseChangeEnum, sort_idx=3):
    FUNC_ADD = "Function added"
    FUNC_REMOVE = "Function removed"
    PARAM_ADD = "Param added"
    PARAM_REMOVE = "Param removed"
    PARAM_REORDER = "Param reordered"
    PARAM_TYPE = "Param type changed"
    FUNC_RETURN = "Return type changed"

    @property
    def consequence(self):
        return {
            FuncChangeEnum.PARAM_ADD: Consequence.SLIENT,
            FuncChangeEnum.PARAM_REMOVE: Consequence.SLIENT,
            FuncChangeEnum.PARAM_TYPE: Consequence.SLIENT,
            FuncChangeEnum.PARAM_REORDER: Consequence.SLIENT,
            FuncChangeEnum.FUNC_RETURN: Consequence.SLIENT,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        cmap = cm.Greens
        return {
            self.PARAM_ADD: cmap(0.3),
            self.PARAM_REMOVE: cmap(0.45),
            self.PARAM_REORDER: cmap(0.6),
            self.PARAM_TYPE: cmap(0.75),
            self.FUNC_RETURN: cmap(0.9),
        }[self]


@dataclass
class FuncReturn(BaseChange, enum=FuncChangeEnum.FUNC_RETURN):
    old: str
    new: str

    def format(self):
        return f"{get_btf_type_str(self.old)} -> {get_btf_type_str(self.new)}"


@dataclass
class ParamRemove(BaseChange, enum=FuncChangeEnum.PARAM_REMOVE):
    name: str
    type: dict

    def format(self):
        return f"{get_btf_type_str(self.type)} {self.name}"


@dataclass
class ParamAdd(BaseChange, enum=FuncChangeEnum.PARAM_ADD):
    name: str
    type: dict

    def format(self):
        return f"{get_btf_type_str(self.type)} {self.name}"


@dataclass
class ParamReorder(BaseChange, enum=FuncChangeEnum.PARAM_REORDER):
    old: dict
    new: dict

    @staticmethod
    def format_param(param):
        return ", ".join(param.keys())

    def format(self):
        return f"{self.format_param(self.old)} -> {self.format_param(self.new)}"


@dataclass
class ParamType(BaseChange, enum=FuncChangeEnum.PARAM_TYPE):
    name: str
    old: dict
    new: dict

    def format(self):
        return f"{get_btf_type_str(self.old)} {self.name} -> {get_btf_type_str(self.new)} {self.name}"


def diff_func(old, new, assert_diff=False) -> List[BaseChange]:
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

    if assert_diff:
        assert result, f"\n{old}\n{new}"

    return result
