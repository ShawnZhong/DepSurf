import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from depsurf.dep import Dep, DepDelta, DepKind, DepStatus
from depsurf.issues import IssueEnum, IssueList
from depsurf.version import Version
from depsurf.version_group import VERSION_DEFAULT, VersionGroup
from depsurf.version_pair import VersionPair

REPORT_KINDS = [
    DepKind.FUNC,
    DepKind.TRACEPOINT,
    DepKind.LSM,
    DepKind.FIELD,
    DepKind.STRUCT,
    DepKind.SYSCALL,
]


Report = Dict[Tuple[VersionGroup, Version], IssueList]
ReportDict = Dict[Dep, Report]


def gen_report(
    deps: Union[List[Dep], Dep],
    version_groups: Union[List[VersionGroup], VersionGroup],
    path: Optional[Path] = None,
) -> ReportDict:
    if isinstance(deps, Dep):
        deps = [deps]
    if isinstance(version_groups, VersionGroup):
        version_groups = [version_groups]
    file = path.open("w") if path else None

    result: ReportDict = {}
    for dep in deps:
        print(f"{dep.kind:12}{dep.name}", file=file)
        if dep.kind not in REPORT_KINDS:
            print("\tSkipped", file=file)
            continue

        issues: Report = {}
        for group in version_groups:
            anchor = None
            versions = []
            for v in group.versions:
                dep_status = v.img.get_dep_status(dep)
                dep_status.print(file=file, nindent=1)
                issues[(group, v)] = dep_status.issues
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
                    issues[(group, p.v2)] += IssueList(IssueEnum.CHANGE)

        result[dep] = issues

    if file:
        file.close()
        logging.info(f"Report saved to {path}")

    return result
