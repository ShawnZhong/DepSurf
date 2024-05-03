import re
from functools import cached_property
from typing import TYPE_CHECKING
import logging


from depsurf.btf import BTF
from depsurf.elf import ObjectFile, SymbolInfo

from .dwarf import DWARF
from .struct import StructInstance
from .tracepoint import Tracepoints

if TYPE_CHECKING:
    from .version import Version


class LinuxImage(ObjectFile):
    cache_enabled = True
    cache = {}

    def __init__(self, version: "Version"):
        if LinuxImage.cache_enabled and version in self.cache:
            raise ValueError(f"Please use LinuxImage.from_* to get an instance")
        self.version = version
        super().__init__(version.vmlinux_path)

    @classmethod
    def from_version(cls, version: "Version"):
        if not cls.cache_enabled:
            return cls(version)
        if version not in cls.cache:
            cls.cache[version] = cls(version)
        return cls.cache[version]

    @classmethod
    def from_path(cls, path):
        from .version import Version

        return cls.from_version(Version.from_path(path))

    @classmethod
    def from_str(cls, name):
        from .version import Version

        return cls.from_version(Version.from_str(name))

    @staticmethod
    def disable_cache():
        LinuxImage.cache_enabled = False
        LinuxImage.cache.clear()

    @staticmethod
    def enable_cache():
        LinuxImage.cache_enabled = True

    @cached_property
    def btf(self) -> BTF:
        return BTF.from_dump(self.version.btf_norm_path)

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
    def comment(self):
        return self.elffile.get_section_by_name(".comment").data().decode()

    @property
    def gcc_version(self):
        return re.search(r"Ubuntu (\d+\.\d+\.\d+)", self.comment).group(1)

    def get_struct_instance(self, name, ptr) -> StructInstance:
        return StructInstance(self, name, ptr)

    def get_bytes(self, addr, size=8) -> bytes:
        if addr in self.relocations:
            assert size == 8
            return self.relocations[addr]
        return super().get_bytes(addr, size)

    @cached_property
    def relocations(self):
        arch = self.elffile["e_machine"]
        if arch not in ("EM_AARCH64", "EM_S390"):
            return {}

        from elftools.elf.dynamic import DynamicSection
        from elftools.elf.relocation import RelocationSection

        relo_sec: RelocationSection = self.elffile.get_section_by_name(".rela.dyn")
        if not relo_sec:
            logging.warning("No .rela.dyn found")
            return {}

        if arch == "EM_S390":
            dynsym: DynamicSection = self.elffile.get_section_by_name(".dynsym")
            if not dynsym:
                logging.warning("No .dynsym found")
                return {}

        constant = 1 << self.elffile.elfclass

        result = {}
        for r in relo_sec.iter_relocations():
            info_type = r["r_info_type"]
            if info_type == 0:
                continue
            elif arch == "EM_AARCH64" and info_type == 1027:
                # R_AARCH64_RELATIVE
                # Ref: https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/arm64/kernel/pi/relocate.c#L15
                val = constant + r["r_addend"]
            elif arch == "EM_S390" and info_type in (12, 22):
                # R_390_RELATIVE and R_390_64
                # Ref:
                # - https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/s390/boot/startup.c#L145
                # - https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/s390/kernel/machine_kexec_reloc.c#L5
                val = r["r_addend"]
                info = r["r_info"]
                sym_idx = info >> 32
                if sym_idx != 0:
                    sym = dynsym.get_symbol(sym_idx)
                    val += sym["st_value"]
            else:
                raise ValueError(f"Unknown relocation type {r}")
            addr = r["r_offset"]
            result[addr] = val.to_bytes(8, self.byteorder)

        return result

    def __repr__(self):
        return f"LinuxImage({self.version.name})"
