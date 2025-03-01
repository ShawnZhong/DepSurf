import logging
import sys
from typing import Dict, List, Optional, TextIO, Tuple, Union

from depsurf.dep import Dep
from depsurf.issues import IssueEnum, IssueList
from depsurf.version import Version
from depsurf.version_group import VERSION_DEFAULT, VersionGroup
from depsurf.version_pair import VersionPair

Report = Dict[Tuple[VersionGroup, Version], IssueList]


def gen_report(
    dep: Dep,
    version_groups: Union[List[VersionGroup], VersionGroup],
    file: Optional[TextIO] = sys.stdout,
) -> Report:
    if isinstance(version_groups, VersionGroup):
        version_groups = [version_groups]

    report: Report = {}
    print(f"{dep.kind:12}{dep.name}", file=file)

    for group in version_groups:
        anchor = None
        versions = []
        for v in group.versions:
            dep_status = v.img.get_dep_status(dep)
            dep_status.print(file=file, nindent=1)
            report[(group, v)] = dep_status.issues
            if dep_status.exists:
                versions.append(v)

        if group == VersionGroup.ARCH:
            anchor = VERSION_DEFAULT
            versions = group.versions
        else:
            if not versions:
                logging.warning(f"Dependency {dep} does not exist in any {group}")
                continue
            anchor = versions[0]

        pairs = [VersionPair(anchor, v) for v in versions if v != anchor]
        for p in pairs:
            dep_diff = p.diff_dep(dep)
            dep_diff.print(file=file, nindent=1)
            if dep_diff.has_changes:
                report[(group, p.v2)] += IssueList(IssueEnum.CHANGE)

    return report
