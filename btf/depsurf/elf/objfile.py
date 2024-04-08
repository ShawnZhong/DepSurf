from pathlib import Path

from depsurf.utils import system

from elftools.elf.elffile import ELFFile


def get_symbol_info(elffile: ELFFile):
    import pandas as pd

    symtab = elffile.get_section_by_name(".symtab")
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
                "value": f"{sym.entry.st_value:x}",
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
                "addr": f"{s.header.sh_addr:x}",
                "data": s.data()[:15],
            }
            for s in elffile.iter_sections()
        ]
    )
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

    def get_symbol_info(self):
        return get_symbol_info(self.elf)

    def get_section_info(self):
        return get_section_info(self.elf)

    def objdump(self):
        system(
            f"{get_objdump_path()} --disassemble --reloc --source {self.path}",
        )

    def hexdump(self):
        system(f"hexdump -C {self.path}")
