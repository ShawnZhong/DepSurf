import logging
from enum import StrEnum
from typing import TYPE_CHECKING, Callable, Dict, Iterator, List

from depsurf.images import ImagePair
from depsurf.version import DEB_PATH, Version

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
            Versions.ALL: VERSIONS_ALL,
            Versions.LTS: VERSIONS_LTS,
            Versions.REGULAR: VERSIONS_REGULAR,
            Versions.REV: VERSIONS_REV,
            Versions.ARCH: VERSIONS_ARCH,
            Versions.FLAVOR: VERSIONS_FLAVOR,
            Versions.TEST: [VERSIONS_LTS[0], VERSIONS_LTS[1]],
            Versions.FIRST: [VERSION_FIRST],
            Versions.LAST: [VERSION_LAST],
            Versions.DEFAULT: [VERSION_DEFAULT],
        }[self]

    @property
    def num_versions(self) -> int:
        return len(self.versions)

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

    def pair_to_str(self, p: ImagePair, sep="→"):
        return f"{self.version_to_str(p.v1)}{sep}{self.version_to_str(p.v2)}"

    def version_to_str(self, v: Version, bold=False):
        if self == Versions.ARCH:
            return v.arch_name
        if self == Versions.FLAVOR:
            return v.flavor_name
        if self == Versions.REV:
            return v.revision
        if self in (Versions.REGULAR, Versions.LTS):
            if bold and v.lts:
                from depsurf.output import bold as bold_fn

                return bold_fn(v.short_version)
            return v.short_version
        return str(v)

    @property
    def labels(self):
        return [self.version_to_str(v, bold=True) for v in self]

    @property
    def pairs(self) -> List[ImagePair]:
        if self in (Versions.REGULAR, Versions.LTS, Versions.REV):
            return [ImagePair(*p) for p in zip(self.versions, self.versions[1:])]

        if len(self) == 1:
            return []

        if len(self) == 2:
            return [ImagePair(self[0], self[1])]

        assert VERSION_DEFAULT not in self.versions
        return [ImagePair(VERSION_DEFAULT, v) for v in self.versions]

    def diff_pairs(self, result_path=None) -> "pd.DataFrame":
        import pandas as pd

        logging.info(f"Diffing {self}")

        results = {}
        for pair in self.pairs:
            name = self.pair_to_str(pair, sep="_")
            path = result_path / name if result_path else None
            logging.info(f"Comparing {name} to {path}")

            name = self.pair_to_str(pair)
            results[(self, name)] = pair.diff(path)

        df = pd.DataFrame(results, index=next(iter(results.values())))
        if result_path:
            df.to_string(result_path / "Summary.txt")
        return df

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
