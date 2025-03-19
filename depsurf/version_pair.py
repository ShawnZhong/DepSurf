from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Tuple

from depsurf.dep import Dep, DepDelta, DepKind
from depsurf.diff import BaseChange, diff_dict
from depsurf.issues import IssueEnum
from depsurf.version import Version


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
            for issue in set(change.issue for change in changes):
                issues[issue] += 1
            # for change in changes:
            #     reasons[change.issue] += 1

        issues[IssueEnum.OLD] = self.old_len
        issues[IssueEnum.NEW] = self.new_len
        issues[IssueEnum.ADD] = len(self.added)
        issues[IssueEnum.REMOVE] = len(self.removed)
        issues[IssueEnum.CHANGE] = len(self.changed)

        return issues

    def iter_issues(self) -> Iterator[Tuple[IssueEnum, int]]:
        return iter(self.issues.items())


@dataclass(frozen=True)
class DiffPairResult:
    v1: Version
    v2: Version
    kind_results: Dict[DepKind, DiffKindResult] = field(default_factory=dict)

    def iter_kinds(self) -> Iterator[Tuple[DepKind, "DiffKindResult"]]:
        return iter(self.kind_results.items())


@dataclass(frozen=True, order=True)
class VersionPair:
    v1: Version
    v2: Version

    def diff(self, kinds: List[DepKind]) -> DiffPairResult:
        return DiffPairResult(
            self.v1, self.v2, {kind: self.diff_kind(kind) for kind in kinds}
        )

    def diff_kind(self, kind: DepKind) -> DiffKindResult:
        dict1 = self.v1.img.get_all_by_kind(kind)
        dict2 = self.v2.img.get_all_by_kind(kind)
        added, removed, common = diff_dict(dict1, dict2)

        changed: Dict[str, List[BaseChange]] = {}

        for name, (old, new) in common.items():
            if old == new:
                continue

            result = kind.differ(old, new)
            # For debugging only
            # if len(result) == 0:
            #     if kind in (DepKind.TRACEPOINT, DepKind.SYSCALL):
            #         continue
            #     logging.error(f"Diff found but no changes: {name}")
            #     logging.error(f"Old: {old}")
            #     logging.error(f"New: {new}")
            #     continue

            # result = [c for c in result if c.issue != IssueEnum.STRUCT_LAYOUT]
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
        changes = []
        if t1 and t2:
            changes = dep.kind.differ(t1, t2)
        # changes = [c for c in changes if c.issue != IssueEnum.STRUCT_LAYOUT]
        return DepDelta(
            v1=self.v1,
            v2=self.v2,
            t1=t1,
            t2=t2,
            changes=changes,
        )

    def __repr__(self):
        return f"({self.v1}, {self.v2})"
