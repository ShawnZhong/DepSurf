import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

from depsurf.dep import Dep, DepDelta, DepKind, DepStatus
from depsurf.version import Version
from depsurf.version_group import VersionGroup, VERSION_DEFAULT
from depsurf.version_pair import VersionPair
from depsurf.issues import IssueList, IssueEnum

REPORT_KINDS = [
    DepKind.FUNC,
    DepKind.TRACEPOINT,
    DepKind.LSM,
    DepKind.FIELD,
    DepKind.STRUCT,
    DepKind.SYSCALL,
]


@dataclass(frozen=True)
class DepReport:
    dep: Dep
    status: Dict[Tuple[VersionGroup, Version], DepStatus]
    delta: Dict[Tuple[VersionGroup, VersionPair], DepDelta]

    @property
    def values(self):
        return list(self.status.values()) + list(self.delta.values())

    @property
    def df(self):
        import pandas as pd

        key = (self.dep.kind, self.dep.name)

        results = {}
        results[key] = {
            ("Status", versions, versions.to_str(v)): d
            for (versions, v), d in self.status.items()
        }
        results[key] |= {
            ("Delta", versions, versions.to_str(p)): d
            for (versions, p), d in self.delta.items()
        }
        return pd.DataFrame(results).T

    def print(self, file=None):
        self.print_status(file=file)
        self.print_delta(file=file)

    def print_status(self, file=None):
        status_str = "|".join(map(str, self.status.values()))
        print(f"\tStatus: {status_str}", file=file)
        for (versions, v), s in self.status.items():
            if s.is_ok:
                continue
            print("\t" + versions.to_str(v), end="", file=file)
            s.print(file=file, nindent=1)
        if all(not s.exists for s in self.status.values()):
            logging.warning(f"Dependency {self.dep} does not exist in any version")

    def print_delta(self, file=None):
        for (group, p), d in self.delta.items():
            if not d:
                continue
            print(f"\t{group.to_str(p.v1)}->{group.to_str(p.v2)}", end="", file=file)
            d.print(file=file, nindent=1)


# def gen_report(
#     deps: Union[List[Dep], Dep],
#     version_groups: Union[List[VersionGroup], VersionGroup],
#     file=None,
# ) -> Dict[Dep, DepReport]:
#     if isinstance(deps, Dep):
#         deps = [deps]
#     if isinstance(version_groups, VersionGroup):
#         version_groups = [version_groups]

#     result = {}
#     for dep in deps:
#         print(f"{dep.kind:12}{dep.name}", file=file)
#         if dep.kind not in REPORT_KINDS:
#             print("\tSkipped", file=file)
#             continue

#         report = DepReport(
#             dep,
#             {
#                 (versions, v): v.img.get_dep_status(dep)
#                 for versions in version_groups
#                 for v in versions
#             },
#             {
#                 (versions, p): p.diff_dep(dep)
#                 for versions in version_groups
#                 for p in versions.pairs
#             },
#         )
#         report.print(file=file)
#         result[dep] = report

#     return result


Report = Dict[Tuple[VersionGroup, Version], IssueList]
ReportDict = Dict[Dep, Report]


def gen_report(
    deps: Union[List[Dep], Dep],
    version_groups: Union[List[VersionGroup], VersionGroup],
    file=None,
) -> ReportDict:
    if isinstance(deps, Dep):
        deps = [deps]
    if isinstance(version_groups, VersionGroup):
        version_groups = [version_groups]

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
                issues[(group, v)] = dep_status.issues
                print(f"\tExist in {group.to_str(v)}: {dep_status.exists}", file=file)
                if dep_status.exists:
                    dep_status.print(file=file, nindent=2)
                    versions.append(v)

            if group == VersionGroup.ARCH:
                anchor = VERSION_DEFAULT
                versions = group.versions
            else:
                anchor = versions[0]

            pairs = [VersionPair(anchor, v) for v in versions]

            for p in pairs:
                dep_diff = p.diff_dep(dep)
                if dep_diff.in_v1 and dep_diff.in_v2:
                    changed = len(dep_diff.changes) != 0
                    print(
                        f"\tChanged from {group.to_str(p.v1)} to {group.to_str(p.v2)}: {changed}",
                        file=file,
                    )
                    if changed:
                        dep_diff.print(file=file, nindent=2)
                        issues[(group, p.v2)] += IssueList(IssueEnum.CHANGE)

        result[dep] = issues

    return result
