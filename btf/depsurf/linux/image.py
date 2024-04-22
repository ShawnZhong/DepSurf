from functools import cached_property
from typing import TYPE_CHECKING

from depsurf.btf import BTF, Kind
from depsurf.elf import ObjectFile, SymbolInfo

from .tracepoint import Tracepoints

if TYPE_CHECKING:
    from .version import BuildVersion


class StructInstance:
    def __init__(self, img: "LinuxImage", name: str, ptr: int):
        self.img = img
        self.name = name
        self.ptr = ptr

        t = img.btf.get_struct(name)
        assert t is not None, f"Could not find struct {name}"

        self.size = t["size"]
        self.members = {m["name"]: m for m in t["members"]}

    def get_offset(self, member_name):
        bits_offset = self.members[member_name]["bits_offset"]
        assert bits_offset % 8 == 0
        return bits_offset // 8

    def get(self, name, size=None) -> int:
        m = self.members[name]
        t = m["type"]
        kind = t["kind"]

        addr = self.ptr + self.get_offset(name)

        if size is None:
            if kind == Kind.PTR:
                size = self.img.ptr_size
            elif kind == Kind.INT:
                size = self.img.btf.data[Kind.INT][t["name"]]["size"]
            else:
                raise NotImplementedError

        return self.img.get_int(addr, size)

    def __getitem__(self, name) -> int:
        return self.get(name)

    def get_bytes(self):
        return self.img.get_bytes(self.ptr, self.size)

    def __repr__(self):
        return f"StructInstance({self.name}, {self.ptr:x}): {self.get_bytes().hex()}"


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
        return Tracepoints(self)

    @cached_property
    def lsm_hooks(self):
        func_names = {
            f"security_{e['name']}"
            for e in self.btf.get_struct("security_hook_heads")["members"]
        }
        all_funcs = self.btf.funcs
        return {k: v for k, v in all_funcs.items() if k in func_names}

    def get_struct_instance(self, name, ptr) -> StructInstance:
        return StructInstance(self, name, ptr)

    def __repr__(self):
        return f"LinuxImage({self.version.name})"
