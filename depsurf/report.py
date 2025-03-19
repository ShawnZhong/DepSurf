import dataclasses
import json
import sys
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Dict, List, TextIO, Tuple

from depsurf.btf import Kind
from depsurf.dep import Dep, DepDelta, DepKind, DepStatus
from depsurf.diff import (
    BaseChange,
    ConfigChange,
    EnumValAdd,
    EnumValChange,
    EnumValRemove,
    FieldAdd,
    FieldRemove,
    FieldType,
    FuncReturn,
    ParamAdd,
    ParamRemove,
    ParamReorder,
    ParamType,
    TraceFormatChange,
)
from depsurf.funcs import FuncGroup
from depsurf.issues import IssueEnum
from depsurf.version import Version
from depsurf.version_group import VersionGroup

IssuesDict = Dict[Tuple[VersionGroup, Version], List[IssueEnum]]


def code_inline(text) -> str:
    return f"<code>{text}</code>"


@dataclass(frozen=True)
class DepReport:
    dep: Dep
    status_dict: Dict[VersionGroup, List[DepStatus]]
    delta_dict: Dict[VersionGroup, List[DepDelta]]

    @classmethod
    def from_groups(cls, dep: Dep, groups: List[VersionGroup]) -> "DepReport":
        return cls(
            dep=dep,
            status_dict={
                group: [version.img.get_dep_status(dep) for version in group.versions]
                for group in groups
            },
            delta_dict={
                group: [pair.diff_dep(dep) for pair in group.pairs] for group in groups
            },
        )

    @classmethod
    def from_group(cls, dep: Dep, group: VersionGroup) -> "DepReport":
        return cls.from_groups(dep, [group])

    @classmethod
    def from_dict(cls, dict: Dict) -> "DepReport":
        return cls(
            dep=Dep.from_dict(dict["dep"]),
            status_dict={
                VersionGroup(group): [
                    DepStatus.from_dict(status) for status in status_list
                ]
                for group, status_list in dict["status_dict"].items()
            },
            delta_dict={
                VersionGroup(group): [DepDelta.from_dict(delta) for delta in delta_list]
                for group, delta_list in dict["delta_dict"].items()
            },
        )

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)

    @classmethod
    def from_dump(cls, path: Path):
        with path.open("r") as f:
            return cls.from_dict(json.load(f))

    def dump_json(self, path: Path):
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as f:
            json.dump(self.to_dict(), f)

    def dump_md(self, path: Path):
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as f:
            self.print(file=f)

    @property
    def issues_dict(self) -> IssuesDict:
        issues_dict = {
            (group, status.version): status.issues
            for group, status_list in self.status_dict.items()
            for status in status_list
        }
        for group, delta_list in self.delta_dict.items():
            has_changes = False
            for delta in delta_list:
                if delta.is_changed:
                    has_changes = True
                if has_changes and delta.t2 is not None:
                    issues_dict[(group, delta.v2)].append(IssueEnum.CHANGE)
        return issues_dict

    def print(self, file: TextIO = sys.stdout):
        print(f"# {self.dep.kind}: {code_inline(self.dep.name)}\n", file=file)

        print("## Status", file=file)

        for group, status_list in self.status_dict.items():
            print(f"<b>{group.name}</b>", file=file)
            print("<ul>", file=file)
            for status in status_list:
                print("<li>", file=file)
                print_status(group, self.dep, status, file=file)
                print("</li>", file=file)
            print("</ul>", file=file)

        print("", file=file)

        print("## Differences", file=file)

        for group, delta_list in self.delta_dict.items():
            if all(delta.is_both_absent for delta in delta_list):
                continue
            print(f"<b>{group.name}</b>", file=file)
            print("<ul>", file=file)
            for delta in delta_list:
                if delta.is_both_absent:
                    continue
                print("<li>", file=file)
                print_delta(group, self.dep, delta, file=file)
                print("</li>", file=file)
            print("</ul>", file=file)

    def _repr_markdown_(self):
        output = StringIO()
        self.print(file=output)
        return output.getvalue()


def type_to_str(obj) -> str:
    assert "kind" in obj, obj
    kind: str = obj["kind"]

    if kind in (Kind.STRUCT, Kind.UNION, Kind.ENUM):
        return f"{kind.lower()} {obj['name']}"
    if kind in (Kind.VOLATILE, Kind.CONST, Kind.RESTRICT):
        return f"{kind.lower()} {type_to_str(obj['type'])}"
    elif kind in (Kind.TYPEDEF, Kind.INT, Kind.VOID):
        return obj["name"]
    elif kind == Kind.PTR:
        t = obj["type"]
        if t["kind"] == Kind.FUNC_PROTO:
            return type_to_str(t)
        elif t["kind"] == Kind.PTR:
            return f"{type_to_str(t)}*"
        else:
            return f"{type_to_str(t)} *"
    elif kind == Kind.ARRAY:
        return f"{type_to_str(obj['type'])}[{obj['nr_elems']}]"
    elif kind == Kind.FUNC_PROTO:
        return f"{type_to_str(obj['ret_type'])}(*)({', '.join(type_to_str(a['type']) for a in obj['params'])})"
    elif kind == Kind.FWD:
        return f"{obj['fwd_kind']} {obj['name']}"
    elif kind == Kind.FUNC:
        result = type_name_to_str(obj["type"]["ret_type"], obj["name"])
        result += "("
        result += ", ".join(
            type_name_to_str(p["type"], p["name"]) for p in obj["type"]["params"]
        )
        result += ");"
        return result
    else:
        raise ValueError(f"Unknown kind: {obj}")


def type_name_to_str(t, name) -> str:
    kind = t["kind"]
    if kind == Kind.PTR:
        if t["type"]["kind"] == Kind.FUNC_PROTO:
            result = type_to_str(t["type"]["ret_type"])
            result += f" (*{name})"
            result += "("
            result += ", ".join(type_to_str(a["type"]) for a in t["type"]["params"])
            result += ")"
            return result
        else:
            return f"{type_to_str(t)}{name}"
    elif kind == Kind.ARRAY:
        return f"{type_to_str(t['type'])} {name}[{t['nr_elems']}]"
    else:
        return f"{type_to_str(t)} {name}"


def print_dep_val(kind: DepKind, val, file: TextIO):
    print("", file=file)

    if isinstance(val, int):
        return

    if kind == DepKind.TRACEPOINT:
        print("Event:", file=file)
        print_dep_val(DepKind.STRUCT, val["struct"], file=file)
        print("Function:", file=file)
        print_dep_val(DepKind.FUNC, val["func"], file=file)
        return

    if "kind" not in val:
        print(f"{type_to_str(val['type'])}{val['name']}", file=file)
        return

    if kind in (DepKind.STRUCT, DepKind.UNION):
        print("```c", file=file)
        print(type_to_str(val) + " {", file=file)
        for field in val["members"]:
            print(f"    {type_name_to_str(field['type'], field['name'])};", file=file)
        print("};", file=file)
        print("```", file=file)
        return

    print("```c", file=file)
    print(type_to_str(val), file=file)
    print("```", file=file)


def print_func_group(g: FuncGroup, file: TextIO):
    print("", file=file)
    print(f"**Collision:** {g.collision_type}\n", file=file)
    print(f"**Inline:** {g.inline_type}\n", file=file)
    print(f"**Transformation:** {g.has_suffix}\n", file=file)

    print("**Instances:**\n", file=file)
    for f in g.funcs:
        print("```", file=file)
        print(f"In {f.file} ({f.addr:x})", file=file)
        print(f"Location: {f.loc}", file=file)
        # print(f"External: {f.external}", file=file)
        print(f"Inline: {f.inline_actual}", file=file)
        if f.caller_inline:
            print("Inline callers:", file=file)
            for caller in f.caller_inline:
                print(f"  - {caller}", file=file)
        if f.caller_func:
            print("Direct callers:", file=file)
            for caller in f.caller_func:
                print(f"  - {caller}", file=file)
        print("```", file=file)

    if g.symbols:
        print("**Symbols:**\n", file=file)
        print("```", file=file)
        for s in g.symbols:
            print(f"{s.addr:x}-{s.addr + s.size:x}: {s.name} ({s.bind})", file=file)
        print("```", file=file)


def print_status(group: VersionGroup, dep: Dep, status: DepStatus, file: TextIO):
    issues_str = (
        ", ".join([issue.value for issue in status.issues]) + " ⚠️"
        if status.issues
        else "✅"
    )

    v = code_inline(group.to_str(status.version))
    title = f"In {v}: {issues_str}"
    if not status.t and not status.func_group:
        print(title, file=file)
        return

    print("<details>", file=file)
    print(f"<summary>{title}</summary>", file=file)

    if status.t:
        print_dep_val(dep.kind, status.t, file=file)

    if status.func_group:
        print_func_group(status.func_group, file=file)

    print("</details>", file=file)


def print_change(change: BaseChange, file: TextIO):
    if isinstance(change, (FieldAdd, FieldRemove)):
        print(code_inline(f"{type_name_to_str(change.type, change.name)}"), file=file)
    elif isinstance(change, (FieldType, ParamType)):
        print(
            code_inline(f"{type_name_to_str(change.old, change.name)}")
            + " ➡️ "
            + code_inline(f"{type_name_to_str(change.new, change.name)}"),
            file=file,
        )
    elif isinstance(change, FuncReturn):
        print(
            code_inline(f"{type_to_str(change.old)}")
            + " ➡️ "
            + code_inline(f"{type_to_str(change.new)}"),
            file=file,
        )
    elif isinstance(change, (ParamRemove, ParamAdd)):
        print(code_inline(f"{type_name_to_str(change.type, change.name)}"), file=file)
    elif isinstance(change, ParamReorder):
        print(
            code_inline(", ".join(change.old.keys()))
            + " ➡️ "
            + code_inline(", ".join(change.new.keys())),
            file=file,
        )
    elif isinstance(change, (TraceFormatChange, ConfigChange)):
        print(
            code_inline(change.old) + " ➡️ " + code_inline(change.new),
            file=file,
        )
    elif isinstance(change, (EnumValAdd, EnumValRemove)):
        print(f"{change.name} = {change.val}", file=file)
    elif isinstance(change, EnumValChange):
        print(f"{change.name} = {change.old_val} -> {change.new_val}", file=file)


def print_delta(group: VersionGroup, dep: Dep, delta: DepDelta, file: TextIO):
    v1 = code_inline(group.to_str(delta.v1))
    v2 = code_inline(group.to_str(delta.v2))

    if delta.is_unchanged:
        print(f"No changes between {v1} and {v2} ✅", file=file)
        return

    if group in (VersionGroup.ARCH, VersionGroup.FLAVOR):
        if delta.is_added:
            print(f"Only exists in {v2} ➕", file=file)
            return
        elif delta.is_removed:
            print(f"Does not exist in {v2} ➖", file=file)
            return

    print("<details>", file=file)
    if delta.is_changed:
        print(f"<summary>Changed between {v1} and {v2} ⚠️</summary>", file=file)
        print("<ul>", file=file)
        for change in delta.changes:
            print("<li>", file=file)
            print(f"<b>{change.issue}. </b>", file=file)
            print_change(change, file=file)
            print("</li>", file=file)
        print("</ul>", file=file)
    elif delta.is_added:
        print(f"<summary>Added between {v1} and {v2} ➕</summary>", file=file)
        print_dep_val(dep.kind, delta.t2, file=file)
    elif delta.is_removed:
        print(f"<summary>Removed between {v1} and {v2} ➖</summary>", file=file)
        print_dep_val(dep.kind, delta.t1, file=file)
    print("</details>", file=file)
