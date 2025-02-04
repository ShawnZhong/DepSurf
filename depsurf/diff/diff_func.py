from dataclasses import dataclass
from typing import List

from depsurf.btf import Kind, get_type_str

from depsurf.issues import IssueEnum
from .common import BaseChange, diff_dict


@dataclass
class FuncReturn(BaseChange, enum=IssueEnum.RETURN_TYPE):
    old: str
    new: str

    def format(self):
        return f"{get_type_str(self.old)} -> {get_type_str(self.new)}"


@dataclass
class ParamRemove(BaseChange, enum=IssueEnum.PARAM_REMOVE):
    name: str
    type: dict

    def format(self):
        return f"{get_type_str(self.type)} {self.name}"


@dataclass
class ParamAdd(BaseChange, enum=IssueEnum.PARAM_ADD):
    name: str
    type: dict

    def format(self):
        return f"{get_type_str(self.type)} {self.name}"


@dataclass
class ParamReorder(BaseChange, enum=IssueEnum.PARAM_REORDER):
    old: dict
    new: dict

    @staticmethod
    def format_param(param):
        return ", ".join(param.keys())

    def format(self):
        return f"{self.format_param(self.old)} -> {self.format_param(self.new)}"


@dataclass
class ParamType(BaseChange, enum=IssueEnum.PARAM_TYPE):
    name: str
    old: dict
    new: dict

    def format(self):
        return f"{get_type_str(self.old)} {self.name} -> {get_type_str(self.new)} {self.name}"


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
