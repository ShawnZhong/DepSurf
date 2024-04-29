from dataclasses import dataclass
from typing import List

from depsurf.btf import Kind, get_btf_type_str

from .cause import BaseCause, BaseCauseEnum, Consequence
from .utils import diff_dict


class StructCauseEnum(BaseCauseEnum, sort_idx=2):
    STRUCT_ADD = "Struct added"
    STRUCT_REMOVE = "Struct removed"
    FIELD_ADD = "Field added"
    FIELD_REMOVE = "Field removed"
    FIELD_TYPE = "Field type changed"

    @property
    def consequence(self):
        return {
            StructCauseEnum.FIELD_ADD: Consequence.COMPILER,
            StructCauseEnum.FIELD_REMOVE: Consequence.COMPILER,
            StructCauseEnum.FIELD_TYPE: Consequence.SLIENT,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        cmap = cm.Purples
        return {
            self.FIELD_ADD: cmap(0.3),
            self.FIELD_REMOVE: cmap(0.5),
            self.FIELD_TYPE: cmap(0.7),
        }[self]


@dataclass
class FieldAdd(BaseCause, enum=StructCauseEnum.FIELD_ADD):
    name: str
    type: dict

    def format(self):
        return f"{get_btf_type_str(self.type)} {self.name}"


@dataclass
class FieldRemove(BaseCause, enum=StructCauseEnum.FIELD_REMOVE):
    name: str
    type: dict

    def format(self):
        return f"{get_btf_type_str(self.type)} {self.name}"


@dataclass
class FieldType(BaseCause, enum=StructCauseEnum.FIELD_TYPE):
    name: str
    old: dict
    new: dict

    def format(self):
        return f"{get_btf_type_str(self.old)} {self.name} -> {get_btf_type_str(self.new)} {self.name}"


def diff_struct_field(old, new, assert_diff=False) -> List[BaseCause]:
    assert old["name"] == new["name"]
    name = old["name"]

    if old["type"] != new["type"]:
        return [FieldType(name=name, old=old["type"], new=new["type"])]

    if assert_diff:
        assert False, f"\n{old}\n{new}"


def diff_struct(old, new, assert_diff=False) -> List[BaseCause]:
    assert old["kind"] == new["kind"]
    assert old["kind"] in (Kind.STRUCT, Kind.UNION), f"{old['kind']}"

    changes = []

    old_members = {m["name"]: m for m in old["members"]}
    new_members = {m["name"]: m for m in new["members"]}

    added, removed, common = diff_dict(old_members, new_members)

    for name, value in added.items():
        changes.append(FieldAdd(name=name, type=value["type"]))

    for name, value in removed.items():
        changes.append(FieldRemove(name=name, type=value["type"]))

    for name, (old_value, new_value) in common.items():
        if old_value["type"] != new_value["type"]:
            changes.append(
                FieldType(name=name, old=old_value["type"], new=new_value["type"])
            )

    # fields changed offset
    offset_changed = False
    old_offset = {name: old_members[name]["bits_offset"] for name in old_members}
    new_offset = {name: new_members[name]["bits_offset"] for name in new_members}
    if old_offset != new_offset or old["size"] != new["size"]:
        offset_changed = True

    if assert_diff:
        assert changes or offset_changed, f"\n{old}\n{new}"
    return changes
