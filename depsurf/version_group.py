import logging
from enum import StrEnum
from typing import TYPE_CHECKING, Dict, Iterator, List, Tuple

from depsurf.version_pair import VersionPair
from depsurf.version import DEB_PATH, Version
from depsurf.dep import DepKind


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
VERSIONS_FLAVOR = sorted(
    [
        v
        for v in VERSIONS_ALL
        if v.flavor != VERSION_DEFAULT.flavor and v.version == VERSION_DEFAULT.version
    ],
    key=lambda x: x.flavor_index,
)
VERSION_FIRST = VERSIONS_ALL[0]
VERSION_LAST = VERSIONS_ALL[-1]

DiffResult = Dict[Tuple["VersionGroup", VersionPair], Dict[Tuple[DepKind, str], int]]


class VersionGroup(StrEnum):
    ALL = "All"
    LTS = "LTS"
    REGULAR = "Regular"
    REV = "Revision"
    ARCH = "Arch"
    FLAVOR = "Flavor"
    TEST = "Test"
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
            VersionGroup.TEST: [VERSIONS_LTS[0], VERSIONS_LTS[1]],
            VersionGroup.FIRST: [VERSION_FIRST],
            VersionGroup.LAST: [VERSION_LAST],
            VersionGroup.DEFAULT: [VERSION_DEFAULT],
        }[self]

    @property
    def num_versions(self) -> int:
        return len(self.versions)

    def pair_to_str(self, p: VersionPair, sep="→") -> str:
        return f"{self.version_to_str(p.v1)}{sep}{self.version_to_str(p.v2)}"

    def version_to_str(self, v: Version) -> str:
        if self == VersionGroup.ARCH:
            return v.arch_name
        if self == VersionGroup.FLAVOR:
            return v.flavor_name
        if self == VersionGroup.REV:
            return str(v.revision)
        if self in (VersionGroup.REGULAR, VersionGroup.LTS):
            return v.short_version
        return str(v)

    def to_str(self, x) -> str:
        if isinstance(x, Version):
            return self.version_to_str(x)
        if isinstance(x, VersionPair):
            return self.pair_to_str(x)
        return str(x)

    @property
    def version_labels(self):
        return [self.version_to_str(v) for v in self]

    @property
    def pair_labels(self):
        return [self.pair_to_str(p) for p in self.pairs]

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

    def diff_pairs(self, kinds: List[DepKind], result_path=None) -> DiffResult:
        logging.info(f"Diffing {self}")

        results: DiffResult = {}
        for pair in self.pairs:
            name = self.pair_to_str(pair, sep="_")
            path = result_path / name if result_path else None
            logging.info(f"Comparing {name} to {path}")
            results[(self, pair)] = pair.diff(result_path=path, kinds=kinds)
        return results

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
