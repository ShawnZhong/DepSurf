from depsurf.btf import BTF
from depsurf.elf import ObjectFile
from .version import BuildVersion

from functools import cached_property


class LinuxImage(ObjectFile):
    def __init__(self, version: BuildVersion):
        self.version = version
        super().__init__(version.vmlinux_path)

    @classmethod
    def from_path(cls, path):
        return cls(BuildVersion.from_path(path))

    @classmethod
    def from_str(cls, name):
        return cls(BuildVersion.from_str(name))

    @cached_property
    def btf(self):
        return BTF(self.version.btf_normalized_path)
