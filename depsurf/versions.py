from enum import StrEnum
from typing import TYPE_CHECKING, Callable, Dict, Iterator, List

from .images import ImagePair
from .version import DEB_PATH, Version

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
VERSION_FIRST = VERSIONS_ALL[0]
VERSION_LAST = VERSIONS_ALL[-1]


class Versions(StrEnum):
    ALL = "All"
    LTS = "LTS"
    REGULAR = "Regular"
    REV = "Revision"
    ARCH = "Arch"
    FLAVOR = "Flavor"
    # Single-version groups
    FIRST = "First"
    LAST = "Last"
    DEFAULT = "Default"

    @property
    def name(self):
        return self.value

    @property
    def versions(self) -> List[Version]:
        return {
            Versions.ALL: VERSIONS_ALL,
            Versions.LTS: [v for v in VERSIONS_REGULAR if v.lts],
            Versions.REGULAR: VERSIONS_REGULAR,
            Versions.REV: VERSIONS_REV,
            Versions.ARCH: [v for v in VERSIONS_ALL if v.arch != "amd64"],
            Versions.FLAVOR: [v for v in VERSIONS_ALL if v.flavor != "generic"],
            Versions.FIRST: [VERSION_FIRST],
            Versions.LAST: [VERSION_LAST],
            Versions.DEFAULT: [VERSION_DEFAULT],
        }[self]

    def __iter__(self) -> Iterator[Version]:
        return iter(self.versions)

    def __len__(self) -> int:
        return len(self.versions)

    def __getitem__(self, key) -> Version:
        return self.versions[key]

    def __repr__(self):
        return f"Versions({self.name}, {self.versions})"

    def __add__(self, other) -> List[Version]:
        return self.versions + other.versions

    def __radd__(self, other) -> List[Version]:
        return other + self.versions

    @property
    def pairs(self) -> List[ImagePair]:
        if self in (Versions.REGULAR, Versions.LTS, Versions.REV):
            return [ImagePair(*p) for p in zip(self.versions, self.versions[1:])]
        else:
            assert VERSION_DEFAULT not in self.versions
            return [ImagePair(VERSION_DEFAULT, v) for v in self.versions]

    def pair_to_str(self, p: ImagePair):
        return f"{self.version_to_str(p.v1)} → {self.version_to_str(p.v2)}"

    def version_to_str(self, v: Version):
        return {
            Versions.ARCH: v.arch_name,
            Versions.FLAVOR: v.flavor_name,
            Versions.REV: v.revision,
            Versions.REGULAR: v.short_version,
            Versions.LTS: v.short_version,
        }[self]

    def get_labels(self, bold=True):
        if self in (Versions.REGULAR, Versions.LTS) and bold:
            from depsurf.output import bold as bold_fn

            return [
                bold_fn(v.short_version) if v.lts else v.short_version for v in self
            ]

        return [self.version_to_str(v) for v in self.versions]

    @property
    def caption(self):
        return {
            Versions.REGULAR: "Linux Kernel Version",
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
