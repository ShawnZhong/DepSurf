from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from depsurf.dep import Dep, DepKind, DepDelta
from depsurf.diff import BaseChange, ChangeEnum, compare_eq, diff_dict
from depsurf.version import Version


@dataclass(frozen=True)
class ImageDiffResult:
    old_len: int
    new_len: int
    added: Dict[str, Dict]
    removed: Dict[str, Dict]
    changed: Dict[str, List[BaseChange]]

    @property
    def reasons(self) -> Dict[BaseChange, int]:
        reasons = {change: 0 for change in ChangeEnum}
        for changes in self.changed.values():
            for change in changes:
                reasons[change.enum] += 1
        return reasons

    @property
    def summary(self) -> Dict[str, int]:
        return {
            "Old": self.old_len,
            "New": self.new_len,
            **self.reasons,
            ChangeEnum.ADD: len(self.added),
            ChangeEnum.REMOVE: len(self.removed),
            ChangeEnum.CHANGE: len(self.changed),
        }

    def print(self, file=None):
        def print_header(name, items):
            title = f" {name} ({len(items)}) "
            print(f"{title:*^80}", file=file)

        print_header("Changed", self.changed)
        for name, changes in self.changed.items():
            print(name, file=file)
            for change in changes:
                print(f"\t{change}", file=file)

        print_header("Added", self.added)
        for name in self.added:
            print(f"\t{name}", file=file)

        print_header("Removed", self.removed)
        for name in self.removed:
            print(f"\t{name}", file=file)

    def save_txt(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            self.print(f)


@dataclass(frozen=True, order=True)
class ImagePair:
    v1: Version
    v2: Version

    def diff(self, result_path: Path = None) -> Dict[Tuple, int]:
        results = {}
        for kind in [DepKind.FUNC, DepKind.STRUCT, DepKind.TRACEPOINT, DepKind.LSM]:
            result = self.diff_kind(kind)
            if result_path:
                result.save_txt(result_path / f"{kind}.log")
            for name, count in result.summary.items():
                results[kind, name] = count

        file = open(result_path / "Summary.txt", "w") if result_path else None
        for (kind, name), count in results.items():
            if count != 0:
                print(f"{kind} {name}: {count}", file=file)
        if file:
            file.close()
        return results

    def diff_kind(self, kind: DepKind) -> ImageDiffResult:
        dict1 = self.v1.img.get_all_by_kind(kind)
        dict2 = self.v2.img.get_all_by_kind(kind)
        added, removed, common = diff_dict(dict1, dict2)

        changed: Dict[str, List[BaseChange]] = {
            name: kind.differ(old, new, assert_diff=False)  # TODO: assert_diff
            for name, (old, new) in common.items()
            if not compare_eq(old, new)
        }

        return ImageDiffResult(
            old_len=len(dict1),
            new_len=len(dict2),
            added=added,
            removed=removed,
            changed=changed,
        )

    def diff_dep(self, dep: Dep) -> DepDelta:
        t1 = self.v1.img.get_dep(dep)
        t2 = self.v2.img.get_dep(dep)
        if t1 is None or t2 is None:
            return DepDelta(in_v1=t1 is not None, in_v2=t2 is not None)
        return DepDelta(changes=dep.kind.differ(t1, t2))

    def __repr__(self):
        return f"({self.v1}, {self.v2})"
