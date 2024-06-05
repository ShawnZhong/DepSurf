import logging
from typing import List, Dict, Tuple, Union

from dataclasses import dataclass

from depsurf.dep import DepStatus, Dep, DepKind, DepDelta
from depsurf.images import ImagePair
from depsurf.version import Version
from depsurf.versions import Versions
from depsurf.issues import IssueEnum

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
    status: Dict[Tuple[Versions, Version], DepStatus]
    delta: Dict[Tuple[Versions, ImagePair], DepDelta]

    def __post_init__(self):
        kind = self.dep.kind
        for delta in self.delta.values():
            if kind == DepKind.FUNC:
                for c in delta.changes:
                    assert c.enum in [
                        IssueEnum.PARAM_ADD,
                        IssueEnum.PARAM_REMOVE,
                        IssueEnum.PARAM_TYPE,
                        IssueEnum.PARAM_REORDER,
                        IssueEnum.RETURN_TYPE,
                    ]
            elif kind == DepKind.STRUCT:
                for c in delta.changes:
                    assert c.enum in [
                        IssueEnum.FIELD_ADD,
                        IssueEnum.FIELD_REMOVE,
                        IssueEnum.FIELD_TYPE,
                    ]
            elif kind == DepKind.FIELD:
                for c in delta.changes:
                    assert c.enum == IssueEnum.FIELD_TYPE

    def print(self, file=None):
        self.print_status(file=file)
        self.print_delta(file=file)

    def print_status(self, file=None):
        status_str = "|".join(map(str, self.status.values()))
        print(f"\tStatus: {status_str}", file=file)
        for (versions, v), s in self.status.items():
            if not s:
                continue
            print("\t" + versions.version_to_str(v), end="", file=file)
            s.print(file=file, nindent=1)
        if all(not s.exists for s in self.status.values()):
            logging.warning(f"Dependency {self.dep} does not exist in any version")

    def print_delta(self, file=None):
        for (versions, v), d in self.delta.items():
            if not d:
                continue
            print("\t" + versions.pair_to_str(v), end="", file=file)
            d.print(file=file, nindent=1)


def gen_report(
    deps: List[Dep], version_groups: List[Versions], file=None
) -> Dict[Dep, DepReport]:
    if isinstance(deps, Dep):
        deps = [deps]
    if isinstance(version_groups, Versions):
        version_groups = [version_groups]

    result = {}
    for dep in deps:
        print(f"{dep.kind:12}{dep.name}", file=file)
        if dep.kind not in REPORT_KINDS:
            print("\tSkipped", file=file)
            continue

        report = DepReport(
            dep,
            {
                (versions, v): v.img.get_dep_status(dep)
                for versions in version_groups
                for v in versions
            },
            {
                (versions, p): p.diff_dep(dep)
                for versions in version_groups
                for p in versions.pairs
            },
        )
        report.print(file=file)
        result[(dep.kind, dep.name)] = report

    return result
