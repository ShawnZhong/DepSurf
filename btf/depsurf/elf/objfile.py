from functools import cached_property
from pathlib import Path

from depsurf.utils import system
from elftools.elf.elffile import ELFFile

from .utils import get_cstr
from .symtab import SymbolInfo


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
