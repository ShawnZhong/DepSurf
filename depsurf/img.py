import re
from functools import cached_property
from typing import Dict

from depsurf.btf import BTF
from depsurf.dep import DepKind, Dep, DepStatus
from depsurf.version import Version
from depsurf.dwarf import FuncGroups
from depsurf.linux import (
    get_relocation,
    StructInstance,
    Sections,
    SymbolTable,
    Tracepoints,
    ObjectFile,
)


class LinuxImage(ObjectFile):
    cache_enabled = True
    cache = {}

    def __init__(self, version: Version):
        if LinuxImage.cache_enabled and version in self.cache:
            raise ValueError(f"Please use LinuxImage.from_* to get an instance")
        self.version = version
        super().__init__(version.vmlinux_path)

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
        assert isinstance(kind, DepKind), kind
        return {
            DepKind.STRUCT: self.btf.structs,
            DepKind.FUNC: self.btf.funcs,
            DepKind.TRACEPOINT: self.tracepoints.data,
            DepKind.LSM: self.lsm_hooks,
            DepKind.UNION: self.btf.unions,
            DepKind.ENUM: self.btf.enums,
        }[kind]

    def get_dep(self, dep: Dep):
        if dep.kind == DepKind.STRUCT_FIELD:
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
            group = self.func_groups.get_group(dep.name)
            if group is None:
                return DepStatus(exists=False)

            sym_group = self.symtab.func_sym_groups.get(dep.name)
            return DepStatus(
                exists=True,
                collision=group.get_collision_type(),
                inline=group.get_inline_type(in_symtab=sym_group is not None),
                suffix=sym_group.has_suffix if sym_group else False,
            )
        else:
            return DepStatus(exists=self.get_dep(dep) is not None)

    @cached_property
    def func_groups(self) -> FuncGroups:
        return FuncGroups.from_dump(self.version.dwarf_funcs_path)

    @cached_property
    def sections(self) -> Sections:
        return Sections(self.elffile)

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
        all_funcs = self.btf.funcs
        return {k: v for k, v in all_funcs.items() if k in func_names}

    @property
    def comment(self):
        return self.elffile.get_section_by_name(".comment").data().decode()

    @property
    def gcc_version(self):
        return re.search(r"Ubuntu (\d+\.\d+\.\d+)", self.comment).group(1)

    @cached_property
    def flags(self):
        dwarfinfo = self.elffile.get_dwarf_info(relocate_dwarf_sections=False)
        main_cu = next(
            cu
            for cu in dwarfinfo.iter_CUs()
            if cu.get_top_DIE().get_full_path().endswith("main.c")
        )
        return main_cu.get_top_DIE().attributes["DW_AT_producer"].value.decode()

    def get_struct_instance(self, name, ptr) -> StructInstance:
        return StructInstance(self, name, ptr)

    def get_bytes(self, addr, size=8) -> bytes:
        if addr in self.relocations:
            assert size == 8
            return self.relocations[addr]
        return super().get_bytes(addr, size)

    @cached_property
    def relocations(self):
        return get_relocation(self.elffile)

    def __repr__(self):
        return f"LinuxImage({self.version.name})"
