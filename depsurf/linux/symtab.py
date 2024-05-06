import json
import logging
from functools import cached_property
from typing import Dict, List

from elftools.elf.elffile import ELFFile, SymbolTableSection

from depsurf.utils import check_result_path


@check_result_path
def dump_symtab(vmlinux_path, result_path):
    with open(vmlinux_path, "rb") as fin:
        elffile = ELFFile(fin)

        symtab: SymbolTableSection = elffile.get_section_by_name(".symtab")
        if symtab is None:
            raise ValueError(
                "No symbol table found. Perhaps this is a stripped binary?"
            )

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


class FuncSymbolGroup:
    def __init__(self, name: str, symbols: List[Dict] = None):
        self.name = name
        self.symbols = symbols if symbols is not None else []

    def add(self, symbol: Dict):
        assert symbol["type"] == "STT_FUNC"
        self.symbols.append(symbol)

    @property
    def has_suffix(self):
        return any("." in sym["name"] for sym in self.symbols)

    def __repr__(self):
        return f"FuncSymbolGroup({self.name}, {len(self.symbols)} symbols)"

    def __iter__(self):
        return iter(self.symbols)


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

    def iter_funcs(self):
        for sym in self.data:
            # Ref: https://github.com/torvalds/linux/commit/9f2899fe36a623885d8576604cb582328ad32b3c
            if sym["type"] == "STT_FUNC" and not sym["name"].startswith("__pfx"):
                yield sym

    def __repr__(self):
        return f"SymbolTable({len(self.data)} symbols)"

    def __iter__(self):
        return iter(self.data)
