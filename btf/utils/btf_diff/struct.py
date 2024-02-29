from enum import Enum
from ..btf import Kind
from .impl import diff_dict, DiffChanges


class StructChange(str, Enum):
    ADD = "Field added"
    REMOVE = "Field removed"
    TYPE = "Field type changed"
    LAYOUT = "Layout changed"

    @property
    def consequence(self):
        from . import Consequence

        return {
            StructChange.ADD: Consequence.COMPILER,
            StructChange.REMOVE: Consequence.COMPILER,
            StructChange.TYPE: Consequence.SLIENT,
            StructChange.LAYOUT: Consequence.CORE,
        }[self]


def diff_struct(old, new):
    assert old["kind"] == new["kind"]
    assert old["kind"] in (Kind.STRUCT, Kind.UNION)

    result = DiffChanges()

    old_members = {m["name"]: m for m in old["members"]}
    new_members = {m["name"]: m for m in new["members"]}

    added, removed, common = diff_dict(old_members, new_members)

    # added field
    if added:
        result.add(
            StructChange.ADD,
            [f"{name:20}: {value['type']}" for name, value in added.items()],
        )

    # removed field
    if removed:
        result.add(
            StructChange.REMOVE,
            [f"{name:20}: {value['type']}" for name, value in removed.items()],
        )

    # fields changed type
    changed_types = {
        name: (old_value["type"], new_value["type"])
        for name, (old_value, new_value) in common.items()
        if old_value["type"] != new_value["type"]
    }
    if changed_types:
        result.add(
            StructChange.TYPE,
            [
                f"{name:20}: {old_type}\n{'':20}->{new_type}"
                for name, (old_type, new_type) in changed_types.items()
            ],
        )

    # fields changed offset
    old_offset = {name: old_members[name]["bits_offset"] for name in old_members}
    new_offset = {name: new_members[name]["bits_offset"] for name in new_members}
    if old_offset != new_offset or old["size"] != new["size"]:
        result.add(
            StructChange.LAYOUT,
            [],
        )

    assert result, f"\n{old}\n{new}"
    return result
