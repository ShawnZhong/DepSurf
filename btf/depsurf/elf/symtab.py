import logging
from functools import cached_property

from depsurf.utils import check_result_path
from elftools.elf.elffile import ELFFile, SymbolTableSection


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

    @classmethod
    def from_elffile(cls, elf: ELFFile):
        return cls(cls.get_symbol_info(elf))

    @classmethod
    def from_dump(cls, path):
        import pandas as pd

        logging.info(f"Loading symbol table from {path}")
        data = pd.read_pickle(path)
        return cls(data)

    def dump(self, result_path):
        self.data.to_pickle(result_path)
        logging.info(f"Saved symbol table to {result_path}")

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

    @cached_property
    def funcs(self):
        return self.data[self.data["type"] == "STT_FUNC"]

    @cached_property
    def funcs_local(self):
        return self.funcs[self.funcs["bind"] == "STB_LOCAL"]

    @cached_property
    def funcs_nonlocal(self):
        # STB_GLOBAL and STB_WEAK
        return self.funcs[self.funcs["bind"] != "STB_LOCAL"]

    @cached_property
    def funcs_renamed(self):
        res = self.funcs[self.funcs["name"].str.contains(r"\.")]
        assert (res["bind"] == "STB_LOCAL").all()
        return res

    def _repr_html_(self):
        return self.data._repr_html_()
