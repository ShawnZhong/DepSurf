from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import List, Literal

from depsurf.paths import DATA_PATH

from . import LinuxImage

DEB_PATH = DATA_PATH / "deb"


@dataclass(order=True, frozen=True)
class Version:
    version_tuple: tuple[int, int, int]
    revision: int
    flavor: str
    arch: str

    @classmethod
    def from_path(cls, path: Path | str):
        return cls.from_str(Path(path).name)

    @classmethod
    def from_str(cls, name: str):
        name = (
            name.removeprefix("linux-image-")
            .removeprefix("unsigned-")
            .removesuffix(".deb")
            .removesuffix(".ddeb")
            .replace("_", "-")
        )

        version, revision, flavor, *others, arch = name.split("-")
        return cls(
            version_tuple=cls.version_to_tuple(version),
            revision=int(revision),
            flavor=flavor,
            arch=arch,
        )

    @staticmethod
    def version_to_str(version_tuple: tuple) -> str:
        return ".".join(map(str, version_tuple))

    @staticmethod
    def version_to_tuple(version: str) -> tuple:
        t = tuple(map(int, version.split(".")))
        if len(t) == 2:
            return t + (0,)
        return t

    @property
    def version(self):
        return self.version_to_str(self.version_tuple)

    @property
    def short_version(self):
        assert self.version_tuple[-1] == 0
        return self.version_to_str(self.version_tuple[:-1])

    @property
    def flavor_name(self):
        return {
            "generic": "Generic",
            "lowlatency": "Lat.",
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "GCP",
            "oracle": "Oracle",
        }[self.flavor]

    @property
    def arch_name(self):
        return {
            "amd64": "x64",
            "arm64": "arm",
            "armhf": "armhf",
            "ppc64el": "ppc",
            "s390x": "s390x",
        }[self.arch]

    @property
    def lts(self):
        return self.version_tuple in [
            (4, 4, 0),
            (4, 15, 0),
            (5, 4, 0),
            (5, 15, 0),
            (6, 8, 0),
        ]

    @property
    def name(self):
        return f"{self.version}-{self.revision}-{self.flavor}-{self.arch}"

    @property
    def deb_path(self):
        return DEB_PATH / f"{self.name}.deb"

    @property
    def vmlinux_deb_path(self):
        return (
            f"./usr/lib/debug/boot/vmlinux-{self.version}-{self.revision}-{self.flavor}"
        )

    @property
    def vmlinux_path(self):
        return DATA_PATH / "vmlinux" / self.name

    @property
    def btf_path(self):
        return DATA_PATH / "btf" / f"{self.name}"

    @property
    def btf_json_path(self):
        return DATA_PATH / "btf_json" / f"{self.name}.json"

    @property
    def btf_header_path(self):
        return DATA_PATH / "btf_header" / f"{self.name}.h"

    @property
    def btf_txt_path(self):
        return DATA_PATH / "btf_txt" / f"{self.name}.txt"

    @property
    def btf_norm_path(self):
        return DATA_PATH / "btf_norm" / f"{self.name}.pkl"

    @property
    def symtab_path(self):
        return DATA_PATH / "symtab" / f"{self.name}.pkl"

    @property
    def tracepoints_path(self):
        return DATA_PATH / "tracepoints" / f"{self.name}.jsonl"

    @property
    def funcs_path(self):
        return DATA_PATH / "funcs" / f"{self.name}.jsonl"

    def __repr__(self):
        return self.name

    @cached_property
    def img(self) -> LinuxImage:
        return LinuxImage.from_version(self)

    # @property
    # def vmlinuz_deb_path(self):
    #     return f"./boot/vmlinuz-{self.version_str}-{self.revision}-{self.flavor}"

    # @property
    # def vmlinuz_path(self):
    #     return DATA_PATH / "vmlinuz" / self.name


def filter_version(
    flavor: str = "generic",
    arch: str = "amd64",
    version: str | tuple = None,
    lts: bool = None,
    revision: Literal["first", "last", "all"] = "first",
) -> List[Version]:
    if isinstance(version, str):
        version_tuple = Version.version_to_tuple(version)
    else:
        version_tuple = version

    results: List[Version] = []
    for bv in VERSIONS_ALL:
        if flavor is not None and bv.flavor != flavor:
            continue
        if arch is not None and bv.arch != arch:
            continue
        if version_tuple is not None and bv.version_tuple != version_tuple:
            continue
        if lts is not None and bv.lts != lts:
            continue
        results.append(bv)

    if revision == "all":
        return results

    revisions = {}
    for bv in results:
        key = (bv.version_tuple, bv.flavor, bv.arch)
        if key not in revisions:
            revisions[key] = bv
        elif revision == "first" and bv.revision < revisions[key].revision:
            revisions[key] = bv
        elif revision == "last" and bv.revision > revisions[key].revision:
            revisions[key] = bv
    return list(revisions.values())


VERSIONS_ALL = sorted(Version.from_path(p) for p in DEB_PATH.iterdir())
VERSIONS_LTS = filter_version(lts=True)
VERSIONS_REGULAR = filter_version()
VERSIONS_REV = filter_version(revision="all", version="5.4.0")
VERSIONS_ARCH = [v for v in VERSIONS_ALL if v.arch not in ("amd64", "s390x")]
VERSIONS_FLAVOR = [v for v in VERSIONS_ALL if v.flavor not in ("generic", "oracle")]
VERSION_54 = filter_version(version="5.4.0")[0]
VERSION_FIRST = VERSIONS_ALL[0]
VERSION_LAST = VERSIONS_ALL[-1]
