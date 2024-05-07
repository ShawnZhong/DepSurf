from enum import StrEnum
from typing import TYPE_CHECKING, Callable, Dict, List

from .version import DEB_PATH, Version
from .images import ImagePair

if TYPE_CHECKING:
    import pandas as pd

VERSIONS_ALL = sorted(Version.from_path(p) for p in DEB_PATH.iterdir())
VERSIONS_REV = [
    v
    for v in VERSIONS_ALL
    if v.version == "5.4.0" and v.arch == "amd64" and v.flavor == "generic"
]
VERSION_DEFAULT = VERSIONS_REV[0]
VERSIONS_REGULAR = sorted(
    [
        v
        for v in VERSIONS_ALL
        if v.arch == "amd64" and v.flavor == "generic" and v.version != "5.4.0"
    ]
    + [VERSION_DEFAULT]
)
VERSIONS_LTS = [v for v in VERSIONS_REGULAR if v.lts]
VERSIONS_ARCH = [v for v in VERSIONS_ALL if v.arch != "amd64"]
VERSIONS_FLAVOR = [v for v in VERSIONS_ALL if v.flavor != "generic"]
VERSION_FIRST = VERSIONS_ALL[0]
VERSION_LAST = VERSIONS_ALL[-1]


class Versions(StrEnum):
    LTS = "lts"
    REG = "reg"
    REV = "rev"
    ARCH = "arch"
    FLAVOR = "flavor"

    @property
    def versions(self):
        return {
            Versions.LTS: VERSIONS_LTS,
            Versions.REG: VERSIONS_REGULAR,
            Versions.REV: VERSIONS_REV,
            Versions.ARCH: VERSIONS_ARCH,
            Versions.FLAVOR: VERSIONS_FLAVOR,
        }[self]

    def __iter__(self):
        return iter(self.versions)

    def __getitem__(self, key):
        return self.versions[key]

    @property
    def pairs(self) -> List[ImagePair]:
        if self in (Versions.REG, Versions.LTS, Versions.REV):
            return [ImagePair(*p) for p in zip(self.versions, self.versions[1:])]
        else:
            assert VERSION_DEFAULT not in self.versions
            return [ImagePair(VERSION_DEFAULT, v) for v in self.versions]

    def to_str(self, arg):
        if isinstance(arg, Version):
            return self.to_str_version(arg)
        if isinstance(arg, ImagePair):
            return self.to_str_pair(arg)
        raise ValueError(f"Cannot convert {arg} to string")

    def to_str_pair(self, p: ImagePair):
        return f"{self.to_str_version(p.v1)} → {self.to_str_version(p.v2)}"

    def to_str_version(self, v: Version, use_bold=False):
        if self in (Versions.REG, Versions.LTS, Versions.REV):
            if use_bold:
                from depsurf.output import bold

                return bold(v.short_version) if v.lts else v.short_version
            return v.short_version

        if self in (Versions.ARCH,):
            return v.arch_name

        if self in (Versions.FLAVOR,):
            return v.flavor_name

        raise ValueError(f"Unknown version type {self}")

    @property
    def caption(self):
        return {
            Versions.REG: "Linux Kernel Version",
            Versions.ARCH: "Arch for Linux 5.4",
            Versions.FLAVOR: "Flavor for Linux 5.4",
        }[self]

    @staticmethod
    def apply(
        fn: Callable[[Version], Dict], groups: List["Versions"]
    ) -> "pd.DataFrame":
        import pandas as pd

        results = {}
        for group in groups:
            for v in group.versions:
                results[(group, v)] = fn(v)

        df = pd.DataFrame(results).T
        return df

    @staticmethod
    def num_versions(groups: List["Versions"]) -> List[int]:
        return [len(g.versions) for g in groups]
