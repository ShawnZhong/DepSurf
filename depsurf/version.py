import dataclasses
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from depsurf.paths import DATA_PATH

if TYPE_CHECKING:
    from .image import LinuxImage

DEB_PATH = DATA_PATH / "ddeb"


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
    def name(self):
        return f"{self.version}-{self.revision}-{self.flavor}-{self.arch}"

    @property
    def short_name(self):
        return f"{self.version}-{self.revision}-{self.flavor}"

    @property
    def flavor_name(self):
        return {
            "generic": "Generic",
            "lowlatency": "Lat",
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "GCP",
            "oracle": "Oracle",
        }[self.flavor]

    @property
    def arch_name(self):
        return {
            "amd64": "x86",
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
    def deb_path(self):
        return DEB_PATH / f"{self.name}.deb"

    @property
    def buildinfo_path(self):
        return DATA_PATH / "buildinfo" / f"{self.name}.deb"

    @property
    def config_path(self):
        return DATA_PATH / "config" / f"{self.name}.config"

    @property
    def config_abs_path(self):
        return f"/usr/lib/linux/{self.short_name}/config"

    @property
    def vmlinux_path(self):
        return DATA_PATH / "vmlinux" / self.name

    @property
    def vmlinux_abs_path(self):
        return f"/usr/lib/debug/boot/vmlinux-{self.short_name}"

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
    def dwarf_funcs_path(self):
        return DATA_PATH / "dwarf_funcs" / f"{self.name}.jsonl"

    @cached_property
    def img(self) -> "LinuxImage":
        from depsurf.image import LinuxImage

        return LinuxImage.from_version(self)

    def __repr__(self):
        return self.name

    def __getstate__(self):
        # avioid pickling the img attribute
        return dataclasses.asdict(self)

    def __setstate__(self, state):
        self.__dict__.update(state)

    # @property
    # def vmlinuz_abs_path(self):
    #     return f"./boot/vmlinuz-{self.short_name}"

    # @property
    # def vmlinuz_path(self):
    #     return DATA_PATH / "vmlinuz" / self.name
