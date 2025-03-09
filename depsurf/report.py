import dataclasses
import json
import sys
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Dict, List, TextIO, Tuple

from depsurf.btf import Kind
from depsurf.dep import Dep, DepDelta, DepStatus
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
from depsurf.issues import IssueEnum
from depsurf.linux import TracepointInfo
from depsurf.version import Version
from depsurf.version_group import VersionGroup

IssueDict = Dict[Tuple[VersionGroup, Version], List[IssueEnum]]


def code_block(text, language: str = "") -> str:
    return f"\n```{language}\n{text}\n```"


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

    def dump(self, path: Path):
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @property
    def issue_dict(self) -> IssueDict:
        issue_dict = {
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
                    issue_dict[(group, delta.v2)].append(IssueEnum.CHANGE)
        return issue_dict

    def print(self, file: TextIO = sys.stdout):
        print(f"# {self.dep.kind}: {code_inline(self.dep.name)}\n", file=file)

        print("## Status", file=file)

        for group, status_list in self.status_dict.items():
            print(f"<b>{group.name}</b>", file=file)
            print("<ul>", file=file)
            for status in status_list:
                print("<li>", file=file)
                print_status(status, file=file)
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
                print_delta(delta, file=file)
                print("</li>", file=file)
            print("</ul>", file=file)

    def _repr_markdown_(self):
        output = StringIO()
        self.print(file=output)
        return output.getvalue()


def type_to_str(obj, full=False) -> str:
    if isinstance(obj, TracepointInfo):
        return str(obj)

    if "kind" not in obj:
        return f"{type_to_str(obj['type'])} {obj['name']}"

    assert "kind" in obj, obj
    kind: str = obj["kind"]

    if kind in (Kind.STRUCT, Kind.UNION):
        result = f"{kind.lower()} {obj['name']}"
        if not full:
            return result

        result += " {"
        for field in obj["members"]:
            result += f"\n    {type_to_str(field['type'])} {field['name']};"
        result += "\n}"
        return result

    if kind in (Kind.ENUM, Kind.VOLATILE, Kind.CONST, Kind.RESTRICT):
        return f"{kind.lower()} {obj['name']}"
    elif kind in (Kind.TYPEDEF, Kind.INT, Kind.VOID):
        return obj["name"]
    elif kind == Kind.PTR:
        if obj["type"]["kind"] == Kind.FUNC_PROTO:
            return type_to_str(obj["type"])
        else:
            return f"{type_to_str(obj['type'])} *"
    elif kind == Kind.ARRAY:
        return f"{type_to_str(obj['type'])}[{obj['nr_elems']}]"
    elif kind == Kind.FUNC_PROTO:
        return f"{type_to_str(obj['ret_type'])} (*)({', '.join(type_to_str(a['type']) for a in obj['params'])})"
    elif kind == Kind.FWD:
        return f"{obj['fwd_kind']} {obj['name']}"
    elif kind == Kind.FUNC:
        result = f"{type_to_str(obj['type']['ret_type'])} {obj['name']}"
        result += "("
        result += ", ".join(
            f"{type_to_str(param['type'])} {param['name']}"
            for param in obj["type"]["params"]
        )
        result += ")"
        return result
    else:
        raise ValueError(f"Unknown kind: {obj}")


def print_status(status: DepStatus, file: TextIO = sys.stdout):
    issues_str = (
        ", ".join([issue.value for issue in status.issues]) + " ❓"
        if status.issues
        else "✅"
    )

    title = f"In {code_inline(status.version)}: {issues_str}"
    if not status.t and not status.func_group:
        print(title, file=file)
        return

    print("<details>", file=file)
    print(f"<summary>{title}</summary>", file=file)

    if status.t:
        print(
            code_block(
                type_to_str(status.t, full=True),
                language="c",
            ),
            file=file,
        )

    if status.func_group:
        print(
            code_block(
                json.dumps(status.func_group.to_dict(), indent=2),
                language="json",
            ),
            file=file,
        )
    print("</details>", file=file)


def print_change(change: BaseChange, file: TextIO = sys.stdout):
    if isinstance(change, (FieldAdd, FieldRemove)):
        print(code_inline(f"{type_to_str(change.type)} {change.name}"), file=file)
    elif isinstance(change, (FieldType, ParamType)):
        print(
            code_inline(f"{type_to_str(change.old)} {change.name}")
            + " ➡️ "
            + code_inline(f"{type_to_str(change.new)} {change.name}"),
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
        print(code_inline(f"{type_to_str(change.type)} {change.name}"), file=file)
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


def print_delta(delta: DepDelta, file: TextIO = sys.stdout):
    if delta.is_unchanged:
        print(
            f"No changes between {code_inline(delta.v1)} and {code_inline(delta.v2)} ✅",
            file=file,
        )
        return

    print("<details>", file=file)
    if delta.is_changed:
        print(
            f"<summary>Changed between {code_inline(delta.v1)} and {code_inline(delta.v2)} ❓</summary>",
            file=file,
        )
        print("<ul>", file=file)
        for change in delta.changes:
            print("<li>", file=file)
            print(f"<b>{change.issue}. </b>", file=file)
            print_change(change, file=file)
            print("</li>", file=file)
        print("</ul>", file=file)
    elif delta.is_added:
        print(
            f"<summary>Added between {code_inline(delta.v1)} and {code_inline(delta.v2)} ➕</summary>",
            file=file,
        )
        print(
            code_block(
                type_to_str(delta.t2, full=True),
                language="c",
            ),
            file=file,
        )
    elif delta.is_removed:
        print(
            f"<summary>Removed between {code_inline(delta.v1)} and {code_inline(delta.v2)} ➖</summary>",
            file=file,
        )
        print(
            code_block(
                type_to_str(delta.t1, full=True),
                language="c",
            ),
            file=file,
        )
    print("</details>", file=file)
