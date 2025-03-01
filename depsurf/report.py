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
    groups: List[VersionGroup]
    status_dict: Dict[Tuple[VersionGroup, Version], DepStatus]
    diff_dict: Dict[Tuple[VersionGroup, Version, Version], DepDelta]

    @staticmethod
    def get_pairs(dep: Dep, group: VersionGroup) -> List[VersionPair]:
        if group == VersionGroup.ARCH:
            return [VersionPair(VERSION_DEFAULT, v) for v in group.versions]
        return [
            VersionPair(v1, v2) for v1, v2 in zip(group.versions, group.versions[1:])
        ]
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
            groups=groups,
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
        for group in self.groups:
            has_changes = False
            for pair in self.get_pairs(self.dep, group):
                diff = self.diff_dict[(group, pair.v1, pair.v2)]
                has_changes = has_changes or diff.has_changes
                if has_changes and diff.in_v2:
                    issue_dict[(group, pair.v2)].append(IssueEnum.CHANGE)
        return issue_dict

    @classmethod
    def from_group(cls, dep: Dep, group: VersionGroup) -> "DepReport":
        return cls.from_groups(dep, [group])

    def print(self, file: Optional[TextIO] = sys.stdout):
        print(f"{self.dep}", file=file)
        for (group, version), status in self.status_dict.items():
            status.print(file=file, nindent=1)
        for (group, v1, v2), diff in self.diff_dict.items():
            diff.print(file=file, nindent=1)
