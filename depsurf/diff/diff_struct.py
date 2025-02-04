from dataclasses import dataclass
from typing import List

from depsurf.btf import Kind, get_type_str
from depsurf.issues import IssueEnum

from .common import BaseChange, diff_dict


@dataclass
class StructLayoutChange(BaseChange, enum=IssueEnum.STRUCT_LAYOUT):
    pass


@dataclass
class FieldAdd(BaseChange, enum=IssueEnum.FIELD_ADD):
    name: str
    type: dict

    def format(self):
        return f"{get_type_str(self.type)} {self.name}"


@dataclass
class FieldRemove(BaseChange, enum=IssueEnum.FIELD_REMOVE):
    name: str
    type: dict

    def format(self):
        return f"{get_type_str(self.type)} {self.name}"


@dataclass
class FieldType(BaseChange, enum=IssueEnum.FIELD_TYPE):
    name: str
    old: dict
    new: dict

    def format(self):
        return f"{get_type_str(self.old)} {self.name} -> {get_type_str(self.new)} {self.name}"


def diff_struct_field(old, new) -> List[BaseChange]:
    assert old["name"] == new["name"]

    if old["type"] != new["type"]:
        return [FieldType(name=old["name"], old=old["type"], new=new["type"])]

    return []


def diff_struct(old, new) -> List[BaseChange]:
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

    def offsets(members):
        return [(name, member["bits_offset"]) for name, member in members.items()]

    if offsets(old_members) != offsets(new_members) or old["size"] != new["size"]:
        changes.append(StructLayoutChange())

    return changes
