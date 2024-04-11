import logging
from functools import cached_property
from pathlib import Path

from depsurf.utils import system, check_result_path
from elftools.elf.elffile import ELFFile, SymbolTableSection

from .utils import get_cstr


@check_result_path
def dump_symtab(vmlinux_path, result_path):
    SymbolInfo.from_elf_path(vmlinux_path).dump(result_path)


class SymbolInfo:
    def __init__(self, data):
        self.data = data

    @classmethod
    def from_elf_path(cls, path):
        with open(path, "rb") as f:
            elf = ELFFile(f)
            return cls.from_elffile(elf)

    def dump(self, result_path):
        self.data.to_pickle(result_path)
        logging.info(f"Saved symbol table to {result_path}")

    @classmethod
    def from_dump(cls, path):
        import pandas as pd

        logging.info(f"Loading symbol table from {path}")
        data = pd.read_pickle(path)
        return cls(data)

    @classmethod
    def from_elffile(cls, elf: ELFFile):
        return cls(cls.get_symbol_info(elf))

    @staticmethod
    def get_symbol_info(elffile: ELFFile):
        import pandas as pd

        symtab: SymbolTableSection = elffile.get_section_by_name(".symtab")
        if symtab is None:
            raise ValueError(
                "No symbol table found. Perhaps this is a stripped binary?"
            )

        logging.info("Loading symbol table")

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
                }
                for sym in symtab.iter_symbols()
            ]
        )

        if (df["local"] == 0).all():
            df = df.drop(columns=["local"])

        return df

    def get_symbols_by_name(self, name: str):
        return self.data[self.data["name"] == name]

    def get_symbols_by_value(self, value: int):
        return self.data[self.data["value"] == value]

    def get_value_by_name(self, name: str) -> int:
        symbols = self.get_symbols_by_name(name)
        if len(symbols) != 1:
            raise ValueError(f"Invalid name {name}: {symbols}")
        return symbols.iloc[0]["value"]

    def get_name_by_value(self, value: int) -> str:
        symbols = self.get_symbols_by_value(value)
        if len(symbols) != 1:
            raise ValueError(f"Invalid value {value}: {symbols}")
        return symbols.iloc[0]["name"]

    def _repr_html_(self):
        return self.data._repr_html_()


class SectionInfo:
    def __init__(self, elffile: ELFFile):
        self.data = self.get_section_info(elffile)

    @staticmethod
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
                    # "data": s.data()[:15],
                }
                for s in elffile.iter_sections()
            ]
        ).set_index("name")
        return df

    @cached_property
    def data_sections(self):
        return list(
            self.data.loc[
                [".data", ".text", ".init.data", ".rodata"], ["addr", "size", "offset"]
            ].itertuples(index=False, name=None)
        )

    def addr_to_offset(self, addr):
        for base, size, file_offset in self.data_sections:
            if base <= addr < base + size:
                return file_offset + addr - base

        raise ValueError(f"Invalid address {addr}")

    def _repr_html_(self):
        return self.data._repr_html_()


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
    def symtab(self) -> SymbolInfo:
        return SymbolInfo.from_elffile(self.elf)

    @cached_property
    def sections(self) -> SectionInfo:
        return SectionInfo(self.elf)

    def get_bytes(self, addr, size=8) -> bytes:
        offset = self.sections.addr_to_offset(addr)
        self.file.seek(offset)
        return self.file.read(size)

    def get_int(self, addr, size) -> int:
        return int.from_bytes(self.get_bytes(addr, size), "little")

    def get_cstr(self, addr, size=512) -> str:
        data = self.get_bytes(addr, size)
        return get_cstr(data, 0)

    def objdump(self):
        system(
            f"{get_objdump_path()} --disassemble --reloc --source {self.path}",
        )

    def hexdump(self):
        system(f"hexdump -C {self.path}")
