from pathlib import Path

from depsurf.utils import system

from elftools.elf.elffile import ELFFile, SymbolTableSection
from .utils import get_cstr
from functools import cached_property


def get_symbol_info(elffile: ELFFile):
    import pandas as pd

    symtab: SymbolTableSection = elffile.get_section_by_name(".symtab")
    if symtab is None:
        raise ValueError("No symbol table found. Perhaps this is a stripped binary?")

    sections = [s.name for s in elffile.iter_sections()]

    df = pd.DataFrame(
        [
            {
                "name": sym.name,
                "section": (
                    sections[sym.entry.st_shndx]
                    if isinstance(sym.entry.st_shndx, int)
                    else sym.entry.st_shndx
                ),
                **sym.entry.st_info,
                **sym.entry.st_other,
                "value": sym.entry.st_value,
                # "value": f"{sym.entry.st_value:x}",
                "size": sym.entry.st_size,
                # **{k: v for k, v in sym.entry.items() if k not in ("st_info", "st_other", "st_name", "st_shndx")},
            }
            for sym in symtab.iter_symbols()
        ]
    )

    if (df["local"] == 0).all():
        df = df.drop(columns=["local"])

    return df


def get_section_info(elffile: ELFFile):
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "name": s.name,
                **{
                    k.removeprefix("sh_"): v
                    for k, v in s.header.items()
                    if k not in ("sh_name", "sh_addr")
                },
                # "addr": f"{s.header.sh_addr:x}",
                "addr": s.header.sh_addr,
                "data": s.data()[:15],
            }
            for s in elffile.iter_sections()
        ]
    ).set_index("name")
    return df


def get_objdump_path():
    import shutil

    canidates = ["llvm-objdump-18", "llvm-objdump", "objdump"]
    for prog in canidates:
        path = shutil.which(prog)
        if path:
            return path
    else:
        raise FileNotFoundError(f"None of {canidates} found")


class ObjectFile:
    def __init__(self, path):
        self.path = Path(path)
        self.file = open(path, "rb")
        self.elf = ELFFile(self.file)

    def __del__(self):
        self.file.close()

    @cached_property
    def symbol_info(self):
        return get_symbol_info(self.elf)

    @cached_property
    def section_info(self):
        return get_section_info(self.elf)

    def get_symbols_by_name(self, name):
        return self.symbol_info[self.symbol_info["name"] == name]

    def get_symbols_by_value(self, value):
        return self.symbol_info[self.symbol_info["value"] == value]

    def get_value_by_name(self, name):
        symbols = self.get_symbols_by_name(name)
        if len(symbols) != 1:
            raise ValueError(f"Invalid name {name}: {symbols}")
        return symbols.iloc[0]["value"]

    def get_name_by_value(self, value):
        symbols = self.get_symbols_by_value(value)
        if len(symbols) != 1:
            raise ValueError(f"Invalid value {value}: {symbols}")
        return symbols.iloc[0]["name"]

    @cached_property
    def data_sections(self):
        return list(
            self.section_info.loc[
                [".data", ".text", ".init.data", ".rodata"], ["addr", "size", "offset"]
            ].itertuples(index=False, name=None)
        )

    def addr_to_offset(self, addr):
        for base, size, file_offset in self.data_sections:
            if base <= addr < base + size:
                return file_offset + addr - base

        raise ValueError(f"Invalid address {addr}")

    def get_bytes(self, addr, size=8) -> bytes:
        offset = self.addr_to_offset(addr)
        self.file.seek(offset)
        return self.file.read(size)

    def get_int64(self, addr) -> int:
        return int.from_bytes(self.get_bytes(addr, 8), "little")

    def get_int32(self, addr) -> int:
        return int.from_bytes(self.get_bytes(addr, 4), "little")

    def get_range(self, start, stop) -> bytes:
        return self.get_bytes(start, stop - start)

    def get_cstr(self, addr):
        offset = self.addr_to_offset(addr)
        self.file.seek(offset)
        data = self.file.read(512)
        return get_cstr(data, 0)

    def objdump(self):
        system(
            f"{get_objdump_path()} --disassemble --reloc --source {self.path}",
        )

    def hexdump(self):
        system(f"hexdump -C {self.path}")
