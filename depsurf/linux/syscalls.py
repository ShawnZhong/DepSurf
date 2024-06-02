import logging
from typing import Iterable
from functools import cached_property

from .filebytes import FileBytes
from .symtab import SymbolTable

SYSCALL_PREFIXES = ["stub_", "sys_", "ppc_", "ppc64_"]


class Syscalls:
    def __init__(self, symtab: SymbolTable, filebytes: FileBytes):
        self.symtab = symtab
        self.filebytes = filebytes

        self.table_addr = None
        self.table_size = None
        self.addr_to_name = {}

        for sym in self.symtab.data:
            if sym["name"] == "sys_call_table":
                assert self.table_addr is None
                assert self.table_size is None
                self.table_addr = sym["value"]
                self.table_size = sym["size"]
                if self.table_size == 0:
                    logging.warning("sys_call_table size is 0. Using hardcoded size")
                    # https://github.com/torvalds/linux/blob/219d54332a09e8d8741c1e1982f5eae56099de85/include/uapi/asm-generic/unistd.h#L855
                    self.table_size = 436 * self.filebytes.ptr_size

            if (
                sym["type"] in ("STT_FUNC", "STT_NOTYPE")
                and any(p in sym["name"] for p in SYSCALL_PREFIXES)
                and (
                    sym["value"] not in self.addr_to_name or sym["bind"] == "STB_GLOBAL"
                )
            ):
                self.addr_to_name[sym["value"]] = sym["name"]

        assert self.table_addr is not None
        assert self.table_size is not None

    def iter_syscall(self) -> Iterable[str]:
        for i, ptr in enumerate(
            range(
                self.table_addr,
                self.table_addr + self.table_size,
                self.filebytes.ptr_size,
            )
        ):
            val = self.filebytes.get_int(ptr, self.filebytes.ptr_size)
            name = self.addr_to_name.get(val)
            if name is None:
                logging.warning(f"Unknown syscall at {i}: {ptr:x} -> {val:x}")
            else:
                for prefix in SYSCALL_PREFIXES:
                    name = name.split(prefix, 1)[-1]
                logging.debug(f"{i}: {ptr:x} -> {val:x} -> {name}")
                yield name, i

    @cached_property
    def syscalls(self):
        return {name: 0 for name, i in self.iter_syscall()}
