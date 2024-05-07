import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from depsurf.dep import Dep, DepKind, DepDelta
from depsurf.diff import BaseChange, GenericChanges, compare_eq, diff_dict
from depsurf.version import Version

if TYPE_CHECKING:
    import pandas as pd


@dataclass(frozen=True)
class ImageDiffResult:
    old_len: int
    new_len: int
    added: Dict[str, Dict]
    removed: Dict[str, Dict]
    changed: Dict[str, List[BaseChange]]

    @property
    def reasons(self) -> List[Tuple[BaseChange, int]]:
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
        result[GenericChanges.ADD] = len(self.added)
        result[GenericChanges.REMOVE] = len(self.removed)
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


class ImagePair:
    def __init__(self, v1: Version, v2: Version):
        self.v1 = v1
        self.v2 = v2
        self.img1 = v1.img
        self.img2 = v2.img

    def diff(self, result_path: Path = None) -> "pd.DataFrame":
        import pandas as pd

        results = {}
        for kind in [DepKind.FUNC, DepKind.STRUCT, DepKind.TRACEPOINT, DepKind.LSM]:
            result = self.diff_kind(self.img1, self.img2, kind)
            if result_path:
                result.save_txt(result_path / f"{kind}.log")
            results[kind] = result.df

        df = pd.concat(results, axis=0)
        if result_path:
            df.to_string(result_path / "Summary.txt")
        return df

    def diff_kind(self, kind: DepKind) -> ImageDiffResult:
        dict1 = self.img1.get_all_by_kind(kind)
        dict2 = self.img2.get_all_by_kind(kind)
        added, removed, common = diff_dict(dict1, dict2)

        changed: Dict[str, List[BaseChange]] = {
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

    def diff_dep(self, dep: Dep) -> DepDelta:
        t1 = self.img1.get_dep(dep)
        t2 = self.img2.get_dep(dep)
        if t1 is None or t2 is None:
            return DepDelta()
        return DepDelta(dep.kind.differ(t1, t2))


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
        results[(group, (v1.name, v2.name))] = ImagePair(v1, v2).diff(path)

    df = pd.concat(results, axis=1)
    df.columns = df.columns.droplevel(-1)
    df.to_string(result_path / "Summary.txt")
    return df
