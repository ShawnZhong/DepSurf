import re
from functools import cached_property
from typing import TYPE_CHECKING

from depsurf.btf import BTF
from depsurf.elf import ObjectFile, SymbolInfo

from .dwarf import DWARF
from .struct import StructInstance
from .tracepoint import Tracepoints

if TYPE_CHECKING:
    from .version import BuildVersion


class LinuxImage(ObjectFile):
    cache_enabled = True
    cache = {}

    def __init__(self, version: "BuildVersion"):
        if LinuxImage.cache_enabled and version in self.cache:
            raise ValueError(f"Please use LinuxImage.from_* to get an instance")
        self.version = version
        super().__init__(version.vmlinux_path)

    @classmethod
    def from_version(cls, version: "BuildVersion"):
        if not cls.cache_enabled:
            return cls(version)
        if version not in cls.cache:
            cls.cache[version] = cls(version)
        return cls.cache[version]

    @classmethod
    def from_path(cls, path):
        from .version import BuildVersion

        return cls.from_version(BuildVersion.from_path(path))

    @classmethod
    def from_str(cls, name):
        from .version import BuildVersion

        return cls.from_version(BuildVersion.from_str(name))

    @staticmethod
    def disable_cache():
        LinuxImage.cache_enabled = False
        LinuxImage.cache.clear()

    @staticmethod
    def enable_cache():
        LinuxImage.cache_enabled = True

    @cached_property
    def btf(self) -> BTF:
        return BTF(self.version.btf_normalized_path)

    @cached_property
    def symtab(self) -> SymbolInfo:
        return SymbolInfo.from_dump(self.version.symtab_path)

    @cached_property
    def tracepoints(self) -> Tracepoints:
        return Tracepoints.from_dump(self.version.tracepoints_path)

    @cached_property
    def dwarf(self):
        return DWARF(self.elffile)

    @cached_property
    def lsm_hooks(self):
        func_names = {
            f"security_{e['name']}"
            for e in self.btf.get_struct("security_hook_heads")["members"]
        }
        all_funcs = self.btf.funcs
        return {k: v for k, v in all_funcs.items() if k in func_names}

    @property
    def gcc_version(self):
        return re.search(r"Ubuntu (\d+\.\d+\.\d+)", self.comment).group(1)

    def get_struct_instance(self, name, ptr) -> StructInstance:
        return StructInstance(self, name, ptr)

    def __repr__(self):
        return f"LinuxImage({self.version.name})"
