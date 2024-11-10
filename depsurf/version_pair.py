from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterator
import logging

from depsurf.dep import Dep, DepKind, DepDelta
from depsurf.diff import BaseChange, diff_dict
from depsurf.version import Version
from depsurf.issues import IssueEnum


@dataclass(frozen=True)
class DiffKindResult:
    kind: DepKind
    old_len: int
    new_len: int
    added: Dict[str, Dict]
    removed: Dict[str, Dict]
    changed: Dict[str, List[BaseChange]]

    @property
    def issues(self) -> Dict[IssueEnum, int]:
        issues = {change: 0 for change in IssueEnum}
        for changes in self.changed.values():
            for issue in set(change.enum for change in changes):
                issues[issue] += 1
            # for change in changes:
            #     reasons[change.enum] += 1

        issues[IssueEnum.OLD] = self.old_len
        issues[IssueEnum.NEW] = self.new_len
        issues[IssueEnum.ADD] = len(self.added)
        issues[IssueEnum.REMOVE] = len(self.removed)
        issues[IssueEnum.CHANGE] = len(self.changed)

        return issues

    def iter_issues(self) -> Iterator[Tuple[IssueEnum, int]]:
        return iter(self.issues.items())

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

    def save_txt(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            self.print(f)


@dataclass(frozen=True)
class DiffPairResult:
    v1: Version
    v2: Version
    kind_results: Dict[DepKind, DiffKindResult] = field(default_factory=dict)

    def iter_kinds(self) -> Iterator[Tuple[DepKind, "DiffKindResult"]]:
        return iter(self.kind_results.items())

    def save_summary(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for kind, result in self.iter_kinds():
                for issue, count in result.iter_issues():
                    if count != 0:
                        print(f"{kind} {issue}: {count}", file=f)


@dataclass(frozen=True, order=True)
class VersionPair:
    v1: Version
    v2: Version

    def diff(
        self, kinds: List[DepKind], result_path: Optional[Path] = None
    ) -> DiffPairResult:
        img_result = DiffPairResult(
            self.v1, self.v2, {kind: self.diff_kind(kind) for kind in kinds}
        )

        if result_path:
            logging.info(f"Saving to {result_path}")
            img_result.save_summary(result_path / "Summary.txt")
            for kind, result in img_result.iter_kinds():
                result.save_txt(result_path / f"{kind}.log")
        return img_result

    def diff_kind(self, kind: DepKind) -> DiffKindResult:
        dict1 = self.v1.img.get_all_by_kind(kind)
        dict2 = self.v2.img.get_all_by_kind(kind)
        added, removed, common = diff_dict(dict1, dict2)

        changed: Dict[str, List[BaseChange]] = {}

        for name, (old, new) in common.items():
            if old == new:
                continue

            result = kind.differ(old, new)
            if len(result) == 0:
                if kind in (DepKind.TRACEPOINT, DepKind.SYSCALL):
                    continue
                logging.error(f"Diff found but no changes: {name}")
                logging.error(f"Old: {old}")
                logging.error(f"New: {new}")
                continue

            result = [c for c in result if c.enum != IssueEnum.STRUCT_LAYOUT]
            if result:
                changed[name] = result

        return DiffKindResult(
            kind=kind,
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
            return DepDelta(
                v1=self.v1, v2=self.v2, in_v1=t1 is not None, in_v2=t2 is not None
            )
        return DepDelta(v1=self.v1, v2=self.v2, changes=dep.kind.differ(t1, t2))

    def __repr__(self):
        return f"({self.v1}, {self.v2})"
