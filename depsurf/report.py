import logging
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, TextIO, Tuple

from depsurf.dep import Dep, DepDelta, DepStatus
from depsurf.issues import IssueEnum
from depsurf.version import Version
from depsurf.version_group import VERSION_DEFAULT, VersionGroup
from depsurf.version_pair import VersionPair

IssueDict = Dict[Tuple[VersionGroup, Version], List[IssueEnum]]


@dataclass(frozen=True)
class DepReport:
    dep: Dep
    status_dict: Dict[Tuple[VersionGroup, Version], DepStatus]
    diff_dict: Dict[Tuple[VersionGroup, Version, Version], DepDelta]

    @staticmethod
    def get_pairs(dep: Dep, group: VersionGroup) -> List[VersionPair]:
        if group == VersionGroup.ARCH:
            return [VersionPair(VERSION_DEFAULT, v) for v in group.versions]
        versions = []
        for v in group.versions:
            if v.img.get_dep_status(dep).exists:
                versions.append(v)
        if not versions:
            logging.warning(f"Dependency {dep} does not exist in any {group}")
            return []
        anchor = versions[0]
        return [VersionPair(anchor, v) for v in versions if v != anchor]

    @classmethod
    def from_groups(cls, dep: Dep, groups: List[VersionGroup]) -> "DepReport":
        return cls(
            dep=dep,
            status_dict={
                (group, version): version.img.get_dep_status(dep)
                for group in groups
                for version in group.versions
            },
            diff_dict={
                (group, pair.v1, pair.v2): pair.diff_dep(dep)
                for group in groups
                for pair in cls.get_pairs(dep, group)
            },
        )

    @property
    def issue_dict(self) -> IssueDict:
        issue_dict = {
            (group, version): status.issues
            for (group, version), status in self.status_dict.items()
        }
        for (group, v1, v2), diff in self.diff_dict.items():
            if diff.has_changes:
                issue_dict[(group, v2)].append(IssueEnum.CHANGE)
        return issue_dict

    @classmethod
    def from_group(cls, dep: Dep, group: VersionGroup) -> "DepReport":
        return cls.from_groups(dep, [group])

    def print(self, file: Optional[TextIO] = sys.stdout):
        print(f"{self.dep.kind:12}{self.dep.name}", file=file)
        for (group, version), status in self.status_dict.items():
            status.print(file=file, nindent=1)
        for (group, v1, v2), diff in self.diff_dict.items():
            diff.print(file=file, nindent=1)
