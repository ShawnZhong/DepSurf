import dataclasses
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .linux_image import LinuxImage

PROJ_PATH = Path(__file__).parent.parent
DATA_PATH = PROJ_PATH / "data"

FLAVOR_NAMES = {
    "generic": "Generic",
    "lowlatency": "low-lat",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "oracle": "Oracle",
}

ARCH_NAMES = {
    "amd64": "x86",
    "arm64": "arm64",
    "armhf": "arm32",
    "ppc64el": "ppc",
    "s390x": "s390",
}


@dataclass(order=True, frozen=True)
class Version:
    version_tuple: tuple[int, int, int]
    flavor: str
    arch: str
    revision: int

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
    def name(self):
        return f"{self.version}-{self.revision}-{self.flavor}-{self.arch}"

    @property
    def short_name(self):
        return f"{self.version}-{self.revision}-{self.flavor}"

    @property
    def flavor_name(self):
        return FLAVOR_NAMES[self.flavor]

    @property
    def flavor_index(self):
        return list(FLAVOR_NAMES.keys()).index(self.flavor)

    @property
    def arch_name(self):
        return ARCH_NAMES[self.arch]

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
    def dbgsym_deb_path(self):
        return DATA_PATH / "image_dbgsym" / f"{self.name}.deb"

    @property
    def image_deb_path(self):
        return DATA_PATH / "image" / f"{self.name}.deb"

    @property
    def modules_deb_path(self):
        return DATA_PATH / "modules" / f"{self.name}.deb"

    @property
    def buildinfo_path(self):
        return DATA_PATH / "buildinfo" / f"{self.name}.deb"

    @property
    def config_path(self):
        return DATA_PATH / "config" / f"{self.name}.config"

    @property
    def vmlinux_path(self):
        return DATA_PATH / "vmlinux" / self.name

    @property
    def vmlinuz_path(self):
        return DATA_PATH / "vmlinuz" / self.name

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
        return DATA_PATH / "symtab" / f"{self.name}.jsonl"

    @property
    def tracepoints_path(self):
        return DATA_PATH / "tracepoints" / f"{self.name}.jsonl"

    @property
    def funcs_path(self):
        return DATA_PATH / "funcs" / f"{self.name}.jsonl"

    @property
    def syscalls_path(self):
        return DATA_PATH / "syscalls" / f"{self.name}.json"

    @cached_property
    def img(self) -> "LinuxImage":
        from depsurf.linux_image import LinuxImage

        return LinuxImage.from_version(self)

    def __repr__(self):
        return self.name

    def __getstate__(self):
        # avioid pickling the img attribute
        return dataclasses.asdict(self)

    def __setstate__(self, state):
        self.__dict__.update(state)
