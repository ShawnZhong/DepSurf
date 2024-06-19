import json
import logging
from functools import cached_property
from typing import Dict, List, Optional

from elftools.elf.elffile import ELFFile, SymbolTableSection

from depsurf.utils import check_result_path
from depsurf.funcs import FuncSymbolGroup


@check_result_path
def dump_symtab(vmlinux_path, result_path):
    with open(vmlinux_path, "rb") as fin:
        elffile = ELFFile(fin)

        symtab = elffile.get_section_by_name(".symtab")
        if symtab is None:
            raise ValueError(
                "No symbol table found. Perhaps this is a stripped binary?"
            )
        assert type(symtab) == SymbolTableSection

        sections = [s.name for s in elffile.iter_sections()]

        with open(result_path, "w") as fout:
            for sym in symtab.iter_symbols():
                entry = {
                    "name": sym.name,
                    "section": (
                        sections[sym.entry.st_shndx]
                        if isinstance(sym.entry.st_shndx, int)
                        else sym.entry.st_shndx
                    ),
                    **sym.entry.st_info,
                    **sym.entry.st_other,
                    "value": sym.entry.st_value,
                    "size": sym.entry.st_size,
                }
                fout.write(json.dumps(entry) + "\n")

        logging.info(f"Saved symtab to {result_path}")


class SymbolTable:
    def __init__(self, data: List[Dict]):
        self.data: List[Dict] = data

    @classmethod
    def from_dump(cls, path):
        data = []
        logging.info(f"Loading symtab from {path}")
        with open(path) as f:
            for line in f:
                data.append(json.loads(line))
        return cls(data)

    @cached_property
    def func_sym_groups(self) -> Dict[str, FuncSymbolGroup]:
        result = {}
        for sym in self.iter_funcs():
            name = sym["name"]
            group_name = name.split(".")[0]
            if group_name not in result:
                result[group_name] = FuncSymbolGroup(group_name)
            result[group_name].add(sym)

        return result

    def get_symbols_by_name(self, name: str):
        return [sym for sym in self.data if sym["name"] == name]

    def get_symbols_by_addr(self, addr: int):
        return [sym for sym in self.data if sym["value"] == addr]

    def iter_funcs(self):
        for sym in self.data:
            # Ref: https://github.com/torvalds/linux/commit/9f2899fe36a623885d8576604cb582328ad32b3c
            if sym["type"] == "STT_FUNC" and not sym["name"].startswith("__pfx"):
                yield sym

    def __repr__(self):
        return f"SymbolTable({len(self.data)} symbols)"

    def __iter__(self):
        return iter(self.data)
