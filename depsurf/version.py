import dataclasses
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .linux_image import LinuxImage

PROJ_PATH = Path(__file__).parent.parent
DATA_PATH = PROJ_PATH / "data"


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
    def dbgsym_download_path(self):
        return DATA_PATH / "download" / "dbgsym" / f"{self.name}.deb"

    @property
    def image_download_path(self):
        return DATA_PATH / "download" / "image" / f"{self.name}.deb"

    @property
    def modules_download_path(self):
        return DATA_PATH / "download" / "modules" / f"{self.name}.deb"

    @property
    def buildinfo_download_path(self):
        return DATA_PATH / "download" / "buildinfo" / f"{self.name}.deb"

    @property
    def config_path(self):
        return DATA_PATH / "dataset" / "config" / f"{self.name}.config"

    @property
    def vmlinux_path(self):
        return DATA_PATH / "intermediate" / "vmlinux" / self.name

    @property
    def vmlinuz_path(self):
        return DATA_PATH / "intermediate" / "vmlinuz" / self.name

    @property
    def raw_btf_path(self):
        return DATA_PATH / "intermediate" / "raw_btf" / f"{self.name}"

    @property
    def raw_btf_json_path(self):
        return DATA_PATH / "intermediate" / "raw_btf" / f"{self.name}.json"

    @property
    def raw_btf_header_path(self):
        return DATA_PATH / "intermediate" / "raw_btf" / f"{self.name}.h"

    @property
    def raw_btf_txt_path(self):
        return DATA_PATH / "intermediate" / "raw_btf" / f"{self.name}.txt"

    @property
    def btf_path(self):
        return DATA_PATH / "dataset" / "btf" / f"{self.name}.pkl"

    @property
    def symtab_path(self):
        return DATA_PATH / "dataset" / "symtab" / f"{self.name}.jsonl"

    @property
    def tracepoints_path(self):
        return DATA_PATH / "dataset" / "tracepoints" / f"{self.name}.jsonl"

    @property
    def func_entries_path(self):
        return DATA_PATH / "intermediate" / "func_entries" / f"{self.name}.jsonl"

    @property
    def func_groups_path(self):
        return DATA_PATH / "dataset" / "func_groups" / f"{self.name}.jsonl"

    @property
    def syscalls_path(self):
        return DATA_PATH / "dataset" / "syscalls" / f"{self.name}.json"

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
