import json
from functools import cached_property
from typing import Dict, Optional

from depsurf.btf import Types
from depsurf.dep import Dep, DepKind, DepStatus
from depsurf.funcs import FuncGroups
from depsurf.linux import FileBytes, SymbolTable, Tracepoints, get_configs
from depsurf.version import Version


class LinuxImage:
    cache_enabled = True
    cache = {}

    def __init__(self, version: Version):
        if LinuxImage.cache_enabled and version in self.cache:
            raise ValueError("Please use LinuxImage.from_* to get an instance")
        self.version = version

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
            return self.struct_types.data
        elif kind == DepKind.FUNC:
            return self.func_types.data
        elif kind == DepKind.TRACEPOINT:
            return self.tracepoints.data
        elif kind == DepKind.LSM:
            return self.lsm_hooks
        elif kind == DepKind.UNION:
            return self.union_types.data
        elif kind == DepKind.ENUM:
            return self.enum_types.data
        elif kind == DepKind.SYSCALL:
            return self.syscalls
        elif kind == DepKind.CONFIG:
            return self.configs
        elif kind == DepKind.KFUNC:
            return self.kfuncs
        raise ValueError(f"Unknown DepKind: {kind}")

    def get_dep(self, dep: Dep) -> Optional[Dict]:
        if dep.kind == DepKind.FIELD:
            struct_name, field_name = dep.name.split("::")
            struct = self.struct_types.get(struct_name)
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
                return DepStatus(version=self.version, t=None)

            return DepStatus(
                version=self.version,
                t=self.get_dep(dep),
                func_group=func_group,
            )
        else:
            return DepStatus(
                version=self.version,
                t=self.get_dep(dep),
            )

    @cached_property
    def filebytes(self):
        return FileBytes(self.version.vmlinux_path)

    @cached_property
    def syscalls(self) -> Dict[str, int]:
        with open(self.version.syscalls_path) as f:
            syscalls = json.load(f)
            return {v: 0 for v in syscalls.values()}

    @cached_property
    def func_groups(self) -> FuncGroups:
        return FuncGroups.from_dump(self.version.func_groups_path)

    @cached_property
    def func_types(self) -> Types:
        return Types.from_dump(self.version.func_types_path)

    @cached_property
    def struct_types(self) -> Types:
        return Types.from_dump(self.version.struct_types_path)

    @cached_property
    def union_types(self) -> Types:
        return Types.from_dump(self.version.union_types_path)

    @cached_property
    def enum_types(self) -> Types:
        return Types.from_dump(self.version.enum_types_path)

    @cached_property
    def int_types(self) -> Types:
        return Types.from_dump(self.version.int_types_path)

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
            for e in self.struct_types["security_hook_heads"]["members"]
        }
        return {
            k.removeprefix("security_"): v
            for k, v in self.func_types.items()
            if k in func_names
        }

    @cached_property
    def kfuncs(self):
        prefix = "__BTF_ID__func__"
        func_names = [
            sym["name"].removeprefix(prefix).rsplit("__", 1)[0]
            for sym in self.symtab.data
            if sym["name"].startswith(prefix)
            if "bpf_lsm_" not in sym["name"]
        ]
        return {k: v for k, v in self.func_types.items() if k in func_names}

    @cached_property
    def configs(self):
        return get_configs(self.version.config_path)

    @cached_property
    def comment(self):
        with open(self.version.comment_path) as f:
            return f.readline().strip()

    def __repr__(self):
        return f"LinuxImage({self.version.name})"
