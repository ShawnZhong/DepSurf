from dataclasses import dataclass
from typing import List

from depsurf.btf import Kind

from .change import BaseChange, ChangeEnum
from .utils import diff_dict


@dataclass
class EnumValAdd(BaseChange, enum=ChangeEnum.VAL_ADD):
    name: str
    val: int

    def format(self):
        return f"{self.name} = {self.val}"


@dataclass
class EnumValRemove(BaseChange, enum=ChangeEnum.VAL_REMOVE):
    name: str
    val: int

    def format(self):
        return f"{self.name} = {self.val}"


@dataclass
class EnumValChange(BaseChange, enum=ChangeEnum.VAL_CHANGE):
    name: str
    old_val: int
    new_val: int

    def format(self):
        return f"{self.name} = {self.old_val} -> {self.new_val}"


def diff_enum(old, new, assert_diff=False) -> List[BaseChange]:
    assert old["kind"] == Kind.ENUM
    assert new["kind"] == Kind.ENUM

    result = []

    old_values = {v["name"]: v for v in old["values"]}
    new_values = {v["name"]: v for v in new["values"]}

    added, removed, common = diff_dict(old_values, new_values)

    for name, value in added.items():
        result.append(EnumValAdd(name=name, val=value["val"]))

    for name, value in removed.items():
        result.append(EnumValRemove(name=name, val=value["val"]))

    changed_values = [
        (name, old_value["val"], new_value["val"])
        for name, (old_value, new_value) in common.items()
        if old_value["val"] != new_value["val"]
    ]
    for name, old_val, new_val in changed_values:
        result.append(EnumValChange(name=name, old_val=old_val, new_val=new_val))

    if assert_diff:
        assert result, f"\n{old}\n{new}"
    return result
