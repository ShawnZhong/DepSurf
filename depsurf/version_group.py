import logging
from enum import StrEnum
from typing import Dict, Iterator, List, Tuple
from pathlib import Path
from dataclasses import dataclass

from depsurf.version_pair import VersionPair, DiffImgResult
from depsurf.version import DATA_PATH, Version
from depsurf.dep import DepKind
from depsurf.issues import IssueEnum


VERSIONS_ALL = sorted(set(Version.from_path(p) for p in DATA_PATH.rglob("*.deb")))
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
        if v.arch == VERSION_DEFAULT.arch
        and v.flavor == VERSION_DEFAULT.flavor
        and v.version != VERSION_DEFAULT.version
    ]
    + [VERSION_DEFAULT]
)
VERSIONS_LTS = [v for v in VERSIONS_REGULAR if v.lts]
VERSIONS_ARCH = [
    v
    for v in VERSIONS_ALL
    if v.arch != VERSION_DEFAULT.arch and v.version == VERSION_DEFAULT.version
]
VERSIONS_FLAVOR = [
    v
    for v in VERSIONS_ALL
    if v.flavor != VERSION_DEFAULT.flavor and v.version == VERSION_DEFAULT.version
]
VERSION_FIRST = VERSIONS_REGULAR[0]
VERSION_LAST = VERSIONS_REGULAR[-1]


@dataclass(frozen=True)
class DiffGroupResult:
    group: "VersionGroup"
    data: Dict[VersionPair, DiffImgResult]

    def iter_pairs(self) -> Iterator[Tuple[VersionPair, DiffImgResult]]:
        return iter(self.data.items())


@dataclass(frozen=True)
class DiffResult:
    data: Dict["VersionGroup", DiffGroupResult]

    def iter_groups(self) -> Iterator[Tuple["VersionGroup", DiffGroupResult]]:
        return iter(self.data.items())


class VersionGroup(StrEnum):
    ALL = "All"
    LTS = "LTS"
    REGULAR = "Regular"
    REV = "Revision"
    ARCH = "Arch"
    FLAVOR = "Flavor"
    TEST = "Test"
    FIRST_LAST = "FirstLast"
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
            VersionGroup.ALL: VERSIONS_ALL,
            VersionGroup.LTS: VERSIONS_LTS,
            VersionGroup.REGULAR: VERSIONS_REGULAR,
            VersionGroup.REV: VERSIONS_REV,
            VersionGroup.ARCH: VERSIONS_ARCH,
            VersionGroup.FLAVOR: VERSIONS_FLAVOR,
            VersionGroup.FIRST_LAST: [VERSION_FIRST, VERSION_LAST],
            VersionGroup.TEST: [VERSIONS_LTS[0], VERSIONS_LTS[1]],
            VersionGroup.FIRST: [VERSION_FIRST],
            VersionGroup.LAST: [VERSION_LAST],
            VersionGroup.DEFAULT: [VERSION_DEFAULT],
        }[self]

    @property
    def num_versions(self) -> int:
        return len(self.versions)

    def to_str(self, v: Version) -> str:
        if self == VersionGroup.ARCH:
            return v.arch
        if self == VersionGroup.FLAVOR:
            return v.flavor
        if self == VersionGroup.REV:
            return str(v.revision)
        if self in (VersionGroup.REGULAR, VersionGroup.LTS, VersionGroup.FIRST_LAST):
            return v.short_version
        return str(v)

    @property
    def pairs(self) -> List[VersionPair]:
        if self in (VersionGroup.REGULAR, VersionGroup.LTS, VersionGroup.REV):
            return [VersionPair(*p) for p in zip(self.versions, self.versions[1:])]

        if len(self) == 1:
            return []

        if len(self) == 2:
            return [VersionPair(self[0], self[1])]

        assert VERSION_DEFAULT not in self.versions
        return [VersionPair(VERSION_DEFAULT, v) for v in self.versions]

    @property
    def num_pairs(self) -> int:
        return len(self.pairs)

    def diff_pairs(self, kinds: List[DepKind], result_path: Path) -> DiffGroupResult:
        logging.info(f"Diffing {self}")
        return DiffGroupResult(
            self,
            {
                pair: pair.diff(
                    kinds,
                    result_path / f"{self.to_str(pair.v1)}_{self.to_str(pair.v2)}",
                )
                for pair in self.pairs
            },
        )

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
