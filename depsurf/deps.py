import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Callable

from depsurf.diff import (
    BaseCause,
    GenericCauses,
    compare_eq,
    diff_dict,
    diff_enum,
    diff_func,
    diff_struct,
    diff_struct_field,
    diff_tracepoint,
)
from depsurf.linux import LinuxImage
from depsurf.version import Version

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


class DepKind(StrEnum):
    STRUCT = "Struct"
    STRUCT_FIELD = "Field"
    FUNC = "Function"
    TRACEPOINT = "Tracepoint"
    LSM = "LSM"
    UNION = "Union"
    ENUM = "Enum"

    # other kinds of hooks supported by BPF
    SYSCALL = "Syscall"
    UPROBE = "uprobe"
    USDT = "USDT"
    PERF_EVENT = "Perf Event"

    @staticmethod
    def from_hook_name(name: str):
        if name.startswith("tracepoint/syscalls/"):
            return DepKind.SYSCALL

        prefix = name.split("/")[0]
        return {
            "kprobe": DepKind.FUNC,
            "kretprobe": DepKind.FUNC,
            "fentry": DepKind.FUNC,
            "fexit": DepKind.FUNC,
            "tp_btf": DepKind.TRACEPOINT,
            "raw_tp": DepKind.TRACEPOINT,
            "tracepoint": DepKind.TRACEPOINT,
            "lsm": DepKind.LSM,
            "uprobe": DepKind.UPROBE,
            "uretprobe": DepKind.UPROBE,
            "usdt": DepKind.USDT,
            "perf_event": DepKind.PERF_EVENT,
        }[prefix]

    def get_kinds(self, img: LinuxImage) -> Dict[str, Dict]:
        return {
            DepKind.STRUCT: img.btf.structs,
            DepKind.FUNC: img.btf.funcs,
            DepKind.TRACEPOINT: img.tracepoints.data,
            DepKind.LSM: img.lsm_hooks,
            DepKind.UNION: img.btf.unions,
            DepKind.ENUM: img.btf.enums,
        }[self]

    def get_kind(self, img: LinuxImage, name: str) -> Dict:
        if self == DepKind.STRUCT_FIELD:
            struct_name, field_name = name.split("::")
            struct = img.btf.structs.get(struct_name)
            if struct is None:
                return None
            for field in struct["members"]:
                if field["name"] == field_name:
                    return field
            return None
        else:
            return self.get_kinds(img).get(name)

    @property
    def differ(self) -> Callable[[Dict, Dict], List[BaseCause]]:
        return {
            DepKind.STRUCT: diff_struct,
            DepKind.STRUCT_FIELD: diff_struct_field,
            DepKind.FUNC: diff_func,
            DepKind.TRACEPOINT: diff_tracepoint,
            DepKind.LSM: diff_func,
            DepKind.UNION: diff_struct,
            DepKind.ENUM: diff_enum,
        }[self]

    def status(self, img: LinuxImage, name: str):
        return self.get_kind(img, name) is not None

    def diff_kind(
        self, img1: LinuxImage, img2: LinuxImage, name: str
    ) -> Optional[bool]:
        t1 = self.get_kind(img1, name)
        t2 = self.get_kind(img2, name)
        if t1 is None or t2 is None:
            return None
        return self.differ(t1, t2)

    def diff_kinds(self, img1: LinuxImage, img2: LinuxImage) -> ImageDiffResult:
        dict1 = self.get_kinds(img1)
        dict2 = self.get_kinds(img2)
        added, removed, common = diff_dict(dict1, dict2)

        changed: Dict[str, List[BaseCause]] = {
            name: self.differ(old, new, assert_diff=False)  # TODO: assert_diff
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

    def __repr__(self):
        return f"'{self.value}'"


def diff_img(img1: LinuxImage, img2: LinuxImage, result_path: Path) -> "pd.DataFrame":
    import pandas as pd

    results = {}
    for dep_kind in [DepKind.FUNC, DepKind.STRUCT, DepKind.TRACEPOINT, DepKind.LSM]:
        result = dep_kind.diff_kinds(img1, img2)
        result.save_txt(result_path / f"{dep_kind}.log")
        results[dep_kind] = result.df

    df = pd.concat(results, axis=0)
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
