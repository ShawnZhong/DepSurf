import json
import re
from functools import cached_property
from pathlib import Path
from typing import Dict, Optional

from elftools.elf.elffile import ELFFile

from depsurf.btf import BTF
from depsurf.dep import Dep, DepKind, DepStatus
from depsurf.funcs import FuncGroups
from depsurf.linux import (
    FileBytes,
    Sections,
    SymbolTable,
    Tracepoints,
    get_configs,
)
from depsurf.version import Version


class LinuxImage:
    cache_enabled = True
    cache = {}

    def __init__(self, version: Version):
        if LinuxImage.cache_enabled and version in self.cache:
            raise ValueError(f"Please use LinuxImage.from_* to get an instance")
        self.version = version
        self.path = Path(version.vmlinux_path)
        self.file = open(version.vmlinux_path, "rb")
        self.elffile = ELFFile(self.file)

    def __del__(self):
        self.file.close()

    @classmethod
    def from_version(cls, version: Version):
        if not cls.cache_enabled:
            return cls(version)
        if version not in cls.cache:
            cls.cache[version] = cls(version)
        return cls.cache[version]

    @staticmethod
    def disable_cache():
        LinuxImage.cache_enabled = False
        LinuxImage.cache.clear()

    @staticmethod
    def enable_cache():
        LinuxImage.cache_enabled = True

    def get_all_by_kind(self, kind: DepKind) -> Dict:
        if kind == DepKind.STRUCT:
            return self.btf.structs
        elif kind == DepKind.FUNC:
            return self.btf.funcs
        elif kind == DepKind.TRACEPOINT:
            return self.tracepoints.data
        elif kind == DepKind.LSM:
            return self.lsm_hooks
        elif kind == DepKind.UNION:
            return self.btf.unions
        elif kind == DepKind.ENUM:
            return self.btf.enums
        elif kind == DepKind.SYSCALL:
            return self.syscalls
        elif kind == DepKind.CONFIG:
            return self.configs
        raise ValueError(f"Unknown DepKind: {kind}")

    def get_dep(self, dep: Dep) -> Optional[Dict]:
        if dep.kind == DepKind.FIELD:
            struct_name, field_name = dep.name.split("::")
            struct = self.btf.structs.get(struct_name)
            if struct is None:
                return None
            for field in struct["members"]:
                if field["name"] == field_name:
                    return field
            return None
        else:
            return self.get_all_by_kind(dep.kind).get(dep.name)

    def get_dep_status(self, dep: Dep) -> DepStatus:
        if dep.kind == DepKind.FUNC:
            func_group = self.func_groups.get_group(dep.name)
            if func_group is None:
                return DepStatus(version=self.version, exists=False)

            sym_group = self.symtab.func_sym_groups.get(dep.name)
            return DepStatus(
                version=self.version,
                exists=True,
                func_group=func_group,
                sym_group=sym_group,
            )
        else:
            return DepStatus(version=self.version, exists=self.get_dep(dep) is not None)

    @cached_property
    def filebytes(self):
        return FileBytes(self.elffile)

    @cached_property
    def sections(self) -> Sections:
        return Sections(self.elffile)

    @cached_property
    def syscalls(self) -> Dict[str, int]:
        with open(self.version.syscalls_path) as f:
            return json.load(f)

    @cached_property
    def func_groups(self) -> FuncGroups:
        return FuncGroups.from_dump(self.version.dwarf_funcs_path)

    @cached_property
    def btf(self) -> BTF:
        return BTF.from_dump(self.version.btf_norm_path)

    @cached_property
    def symtab(self) -> SymbolTable:
        return SymbolTable.from_dump(self.version.symtab_path)

    @cached_property
    def tracepoints(self) -> Tracepoints:
        return Tracepoints.from_dump(self.version.tracepoints_path)

    @cached_property
    def lsm_hooks(self):
        func_names = {
            f"security_{e['name']}"
            for e in self.btf.get_struct("security_hook_heads")["members"]
        }
        return {k: v for k, v in self.btf.funcs.items() if k in func_names}

    @cached_property
    def configs(self):
        return get_configs(self.version.config_path)

    @property
    def gcc_version(self):
        comment = self.elffile.get_section_by_name(".comment").data().decode()
        return re.search(r"Ubuntu (\d+\.\d+\.\d+)", comment).group(1)

    @cached_property
    def flags(self):
        dwarfinfo = self.elffile.get_dwarf_info(relocate_dwarf_sections=False)
        main_cu = next(
            cu
            for cu in dwarfinfo.iter_CUs()
            if cu.get_top_DIE().get_full_path().endswith("main.c")
        )
        return main_cu.get_top_DIE().attributes["DW_AT_producer"].value.decode()

    def __repr__(self):
        return f"LinuxImage({self.version.name})"
