import json
import logging
from typing import Dict, List
from pathlib import Path

from elftools.elf.sections import SymbolTableSection
from elftools.elf.elffile import ELFFile

from depsurf.utils import manage_result_path


@manage_result_path
def dump_symtab(vmlinux_path: Path, result_path: Path):
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

    def get_symbols_by_name(self, name: str):
        return [sym for sym in self.data if sym["name"] == name]

    def get_symbols_by_addr(self, addr: int):
        return [sym for sym in self.data if sym["value"] == addr]

    def __repr__(self):
        return f"SymbolTable({len(self.data)} symbols)"

    def __iter__(self):
        return iter(self.data)
