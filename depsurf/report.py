import logging
from pathlib import Path
from typing import List, Dict, Tuple, Union

from depsurf.dep import DepStatus, Dep, DepKind, DepDelta
from depsurf.versions import Versions

REPORT_KINDS = [
    DepKind.FUNC,
    DepKind.TRACEPOINT,
    DepKind.LSM,
    DepKind.STRUCT_FIELD,
    DepKind.STRUCT,
]


def gen_report(
    deps: List[Dep], version_groups: List[Versions], path: Path = None
) -> Dict[Dep, Dict[Tuple[str, str], Union[DepStatus, DepDelta]]]:
    if isinstance(deps, Dep):
        deps = [deps]
    if isinstance(version_groups, Versions):
        version_groups = [version_groups]

    file = path.open("w") if path else None

    result = {}
    for dep in deps:
        print(f"{dep.kind:12}{dep.name}", file=file)
        if dep.kind not in REPORT_KINDS:
            print("\tSkipped", file=file)
            continue

        result[dep] = report_dep(dep, version_groups, file)

    if path:
        file.close()
        logging.info(f"Report saved to {path}")

    return result


def report_dep(dep: Dep, version_groups: List[Versions], file=None):
    # Status
    status: Dict[Tuple, DepStatus] = {}
    for versions in version_groups:
        status |= {
            ("Status", versions, versions.version_to_str(v)): v.img.get_dep_status(dep)
            for v in versions
        }
    status_str = "|".join(map(str, status.values()))
    print(f"\tStatus: {status_str}", file=file)
    for (_, _, v), s in status.items():
        if not s:
            continue
        print("\t" + v, end="", file=file)
        s.print(file=file, nindent=1)
    if all(not s.exists for s in status.values()):
        logging.warning(f"Dependency {dep} does not exist in any version")

    # Delta
    delta: Dict[Tuple, DepDelta] = {}
    for versions in version_groups:
        delta |= {
            ("Delta", versions, versions.pair_to_str(p)): p.diff_dep(dep)
            for p in versions.pairs
        }
    for (_, _, v), d in delta.items():
        if not d:
            continue
        print("\t" + v, end="", file=file)
        d.print(file=file, nindent=1)

    return status | delta
