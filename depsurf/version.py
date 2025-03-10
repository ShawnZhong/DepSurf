import dataclasses
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .linux_image import LinuxImage

from .paths import DATASET_PATH, DOWNLOAD_PATH, INTERMEDIATE_PATH


@dataclass(order=True, frozen=True)
class Version:
    version_tuple: tuple[int, int, int]
    flavor: str
    arch: str
    revision: int

    @classmethod
    def from_path(cls, path: Path | str):
        return cls.from_str(Path(path).stem)

    @classmethod
    def from_str(cls, name: str):
        name = (
            name.removeprefix("linux-image-")
            .removeprefix("unsigned-")
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
        return DOWNLOAD_PATH / "dbgsym" / f"{self.name}.deb"

    @property
    def image_download_path(self):
        return DOWNLOAD_PATH / "image" / f"{self.name}.deb"

    @property
    def modules_download_path(self):
        return DOWNLOAD_PATH / "modules" / f"{self.name}.deb"

    @property
    def buildinfo_download_path(self):
        return DOWNLOAD_PATH / "buildinfo" / f"{self.name}.deb"

    @property
    def config_path(self):
        return DATASET_PATH / "config" / f"{self.name}.config"

    @property
    def vmlinux_path(self):
        return INTERMEDIATE_PATH / "vmlinux" / self.name

    @property
    def vmlinuz_path(self):
        return INTERMEDIATE_PATH / "vmlinuz" / self.name

    @property
    def btf_path(self):
        return INTERMEDIATE_PATH / "btf" / f"{self.name}"

    @property
    def btf_json_path(self):
        return INTERMEDIATE_PATH / "btf" / f"{self.name}.json"

    @property
    def btf_header_path(self):
        return INTERMEDIATE_PATH / "btf" / f"{self.name}.h"

    @property
    def btf_txt_path(self):
        return INTERMEDIATE_PATH / "btf" / f"{self.name}.txt"

    @property
    def func_types_path(self):
        return DATASET_PATH / "types_func" / f"{self.name}.jsonl"

    @property
    def struct_types_path(self):
        return DATASET_PATH / "types_struct" / f"{self.name}.jsonl"

    @property
    def union_types_path(self):
        return DATASET_PATH / "types_union" / f"{self.name}.jsonl"

    @property
    def enum_types_path(self):
        return DATASET_PATH / "types_enum" / f"{self.name}.jsonl"

    @property
    def int_types_path(self):
        return DATASET_PATH / "types_int" / f"{self.name}.jsonl"

    @property
    def symtab_path(self):
        return DATASET_PATH / "symtab" / f"{self.name}.jsonl"

    @property
    def tracepoints_path(self):
        return DATASET_PATH / "tracepoints" / f"{self.name}.jsonl"

    @property
    def func_entries_path(self):
        return INTERMEDIATE_PATH / "func_entries" / f"{self.name}.jsonl"

    @property
    def func_groups_path(self):
        return DATASET_PATH / "func_groups" / f"{self.name}.jsonl"

    @property
    def syscalls_path(self):
        return DATASET_PATH / "syscalls" / f"{self.name}.json"

    @property
    def comment_path(self):
        return DATASET_PATH / "comment" / f"{self.name}.txt"

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
