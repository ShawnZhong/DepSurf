from depsurf.btf import Kind
from depsurf.cause import StructChange

from .changes import DiffChanges
from .utils import diff_dict


def diff_struct(old, new, assert_diff=False):
    assert old["kind"] == new["kind"]
    assert old["kind"] in (Kind.STRUCT, Kind.UNION)

    changes = DiffChanges()

    old_members = {m["name"]: m for m in old["members"]}
    new_members = {m["name"]: m for m in new["members"]}

    added, removed, common = diff_dict(old_members, new_members)

    # added field
    if added:
        changes.add(
            StructChange.ADD,
            [(name, value["type"]) for name, value in added.items()],
        )

    # removed field
    if removed:
        changes.add(
            StructChange.REMOVE,
            [(name, value["type"]) for name, value in removed.items()],
        )

    # fields changed type
    changed_types = [
        (name, old_value["type"], new_value["type"])
        for name, (old_value, new_value) in common.items()
        if old_value["type"] != new_value["type"]
    ]
    if changed_types:
        changes.add(StructChange.TYPE, changed_types)

    # fields changed offset
    offset_changed = False
    old_offset = {name: old_members[name]["bits_offset"] for name in old_members}
    new_offset = {name: new_members[name]["bits_offset"] for name in new_members}
    if old_offset != new_offset or old["size"] != new["size"]:
        # result.add(StructChange.LAYOUT, [])
        offset_changed = True

    if assert_diff:
        assert changes or offset_changed, f"\n{old}\n{new}"
    return changes
