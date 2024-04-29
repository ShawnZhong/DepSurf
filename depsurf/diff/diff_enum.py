from dataclasses import dataclass
from typing import List

from depsurf.btf import Kind

from .cause import BaseCause, BaseCauseEnum, Consequence
from .utils import diff_dict


class EnumCauseEnum(BaseCauseEnum, sort_idx=4):
    ENUM_ADD = "Enum added"
    ENUM_REMOVE = "Enum removed"
    VAL_ADD = "Value added"
    VAL_REMOVE = "Value removed"
    VAL_CHANGE = "Value changed"

    @property
    def consequence(self):
        return {
            EnumCauseEnum.VAL_ADD: Consequence.COMPILER,
            EnumCauseEnum.VAL_REMOVE: Consequence.COMPILER,
            EnumCauseEnum.VAL_CHANGE: Consequence.CORE,
        }[self]


@dataclass
class EnumValAdd(BaseCause, enum=EnumCauseEnum.VAL_ADD):
    name: str
    val: int

    def format(self):
        return f"{self.name} = {self.val}"


@dataclass
class EnumValRemove(BaseCause, enum=EnumCauseEnum.VAL_REMOVE):
    name: str
    val: int

    def format(self):
        return f"{self.name} = {self.val}"


@dataclass
class EnumValChange(BaseCause, enum=EnumCauseEnum.VAL_CHANGE):
    name: str
    old_val: int
    new_val: int

    def format(self):
        return f"{self.name} = {self.old_val} -> {self.new_val}"


def diff_enum(old, new, assert_diff=False) -> List[BaseCause]:
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
