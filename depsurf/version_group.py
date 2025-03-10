from enum import StrEnum
from typing import Dict, Iterator, List

from .paths import DATASET_PATH
from .version import Version
from .version_pair import DiffPairResult, VersionPair

VERSION_DEFAULT = Version(
    version_tuple=(5, 4, 0), flavor="generic", arch="amd64", revision=26
)
VERSIONS_ALL = sorted(set(Version.from_path(p) for p in DATASET_PATH.rglob("*.jsonl")))
VERSIONS_REV = [
    v
    for v in VERSIONS_ALL
    if v.version_tuple == VERSION_DEFAULT.version_tuple
    and v.arch == VERSION_DEFAULT.arch
    and v.flavor == VERSION_DEFAULT.flavor
]
VERSIONS_REGULAR = sorted(
    [
        v
        for v in VERSIONS_ALL
        if v.arch == VERSION_DEFAULT.arch
        and v.flavor == VERSION_DEFAULT.flavor
        and v.version_tuple != VERSION_DEFAULT.version_tuple
    ]
    + [VERSION_DEFAULT]
)
VERSIONS_LTS = [
    v
    for v in VERSIONS_REGULAR
    if v.version_tuple
    in [
        (4, 4, 0),
        (4, 15, 0),
        (5, 4, 0),
        (5, 15, 0),
        (6, 8, 0),
    ]
]
VERSIONS_ARCH = [
    v
    for v in VERSIONS_ALL
    if v.arch != VERSION_DEFAULT.arch
    and v.version_tuple == VERSION_DEFAULT.version_tuple
]
VERSIONS_FLAVOR = [
    v
    for v in VERSIONS_ALL
    if v.flavor != VERSION_DEFAULT.flavor
    and v.version_tuple == VERSION_DEFAULT.version_tuple
]


class VersionGroup(StrEnum):
    ALL = "All"
    LTS = "LTS"
    REGULAR = "Regular"
    REV = "Revision"
    ARCH = "Arch"
    FLAVOR = "Flavor"

    @property
    def name(self):
        return self.value

    @property
    def versions(self) -> List[Version]:
        return {
            VersionGroup.ALL: VERSIONS_ALL,
            VersionGroup.LTS: VERSIONS_LTS,
            VersionGroup.REGULAR: VERSIONS_REGULAR,
            VersionGroup.REV: VERSIONS_REV,
            VersionGroup.ARCH: VERSIONS_ARCH,
            VersionGroup.FLAVOR: VERSIONS_FLAVOR,
        }[self]

    @property
    def pairs(self) -> List[VersionPair]:
        if self in (VersionGroup.ARCH, VersionGroup.FLAVOR):
            return [VersionPair(VERSION_DEFAULT, v) for v in self.versions]
        if self in (VersionGroup.LTS, VersionGroup.REGULAR, VersionGroup.REV):
            return [
                VersionPair(v1, v2) for v1, v2 in zip(self.versions, self.versions[1:])
            ]
        raise ValueError(f"Unknown group: {self}")

    def to_str(self, v: Version) -> str:
        if self == VersionGroup.ARCH:
            return v.arch
        if self == VersionGroup.FLAVOR:
            return v.flavor
        if self == VersionGroup.REV:
            return str(v.revision)
        if self in (VersionGroup.REGULAR, VersionGroup.LTS):
            return v.short_version
        return str(v)

    def __iter__(self) -> Iterator[Version]:
        return iter(self.versions)

    def __len__(self) -> int:
        return len(self.versions)

    def __getitem__(self, key) -> Version:
        return self.versions[key]

    def __repr__(self):
        return f"Versions({self.name})"

    def __add__(self, other) -> List[Version]:
        return self.versions + other.versions

    def __radd__(self, other) -> List[Version]:
        return other + self.versions


DiffGroupResult = Dict[VersionPair, DiffPairResult]
DiffResult = Dict[VersionGroup, DiffGroupResult]
