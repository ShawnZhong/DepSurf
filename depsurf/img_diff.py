import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from depsurf.dep import Dep, DepKind
from depsurf.diff import BaseCause, GenericCauses, compare_eq, diff_dict
from depsurf.version import Version

from .img import LinuxImage

if TYPE_CHECKING:
    import pandas as pd


@dataclass(frozen=True)
class ImageDiffResult:
    old_len: int
    new_len: int
    added: Dict[str, Dict]
    removed: Dict[str, Dict]
    changed: Dict[str, List[BaseCause]]

    @property
    def reasons(self) -> List[Tuple[BaseCause, int]]:
        reasons = defaultdict(int)
        for changes in self.changed.values():
            for change in changes:
                reasons[change.enum] += 1
        reasons = sorted(reasons.items(), key=lambda x: x[0].sort_idx)
        return reasons

    @property
    def df(self) -> "pd.DataFrame":
        import pandas as pd

        result = {}
        result["Old"] = self.old_len
        result[GenericCauses.ADD] = len(self.added)
        result[GenericCauses.REMOVE] = len(self.removed)
        for cause, count in self.reasons:
            result[cause] = count

        return pd.DataFrame(result, index=["Count"]).T

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


def diff_img_by_kind(
    img1: LinuxImage, img2: LinuxImage, kind: DepKind
) -> ImageDiffResult:
    dict1 = img1.get_all_by_kind(kind)
    dict2 = img2.get_all_by_kind(kind)
    added, removed, common = diff_dict(dict1, dict2)

    changed: Dict[str, List[BaseCause]] = {
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


def diff_img(
    img1: LinuxImage, img2: LinuxImage, result_path: Path = None
) -> "pd.DataFrame":
    import pandas as pd

    results = {}
    for dep_kind in [DepKind.FUNC, DepKind.STRUCT, DepKind.TRACEPOINT, DepKind.LSM]:
        result = diff_img_by_kind(img1, img2, dep_kind)
        if result_path:
            result.save_txt(result_path / f"{dep_kind}.log")
        results[dep_kind] = result.df

    df = pd.concat(results, axis=0)
    if result_path:
        df.to_string(result_path / "Summary.txt")
    return df


def diff_img_pairs(
    group: str,
    pairs: List[Tuple[Version, Version]],
    result_path: Path,
) -> "pd.DataFrame":
    import pandas as pd

    logging.info(f"Diffing {group}")

    results = {}
    for v1, v2 in pairs:
        path = result_path / f"{v1}_{v2}"
        logging.info(f"Comparing {v1} and {v2} to {path}")
        results[(group, (v1.name, v2.name))] = diff_img(v1.img, v2.img, path)

    df = pd.concat(results, axis=1)
    df.columns = df.columns.droplevel(-1)
    df.to_string(result_path / "Summary.txt")
    return df


def diff_dep(img1: "LinuxImage", img2: "LinuxImage", dep: Dep) -> Optional[bool]:
    t1 = img1.get_dep(dep)
    t2 = img2.get_dep(dep)
    if t1 is None or t2 is None:
        return None
    return dep.kind.differ(t1, t2)
