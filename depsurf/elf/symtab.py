import logging
from functools import cached_property
from typing import TYPE_CHECKING

from depsurf.utils import check_result_path
from elftools.elf.elffile import ELFFile, SymbolTableSection

if TYPE_CHECKING:
    import pandas as pd


@check_result_path
def dump_symtab(vmlinux_path, result_path):
    SymbolInfo.from_elf_path(vmlinux_path).dump(result_path)


class SymbolInfo:
    def __init__(self, data: "pd.DataFrame"):
        import pandas as pd

        self.data: pd.DataFrame = data

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

        logging.info(f"Loading symtab from {path}")
        data = pd.read_pickle(path)
        return cls(data)

    def dump(self, result_path):
        self.data.to_pickle(result_path)
        logging.info(f"Saved symtab to {result_path}")

    @staticmethod
    def get_symbol_info(elffile: ELFFile) -> "pd.DataFrame":
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

    def get_value_by_name(self, name: str) -> int:
        symbols = self.data[self.data["name"] == name]
        if len(symbols) != 1:
            raise ValueError(f"Invalid name {name}: {symbols}")
        return int(symbols.iloc[0]["value"])

    @cached_property
    def objects(self) -> "pd.DataFrame":
        return self.data[self.data["type"] == "STT_OBJECT"]

    @cached_property
    def funcs(self) -> "pd.DataFrame":
        funcs = self.data[self.data["type"] == "STT_FUNC"]
        # Ref: https://github.com/torvalds/linux/commit/9f2899fe36a623885d8576604cb582328ad32b3c
        return funcs[~funcs["name"].str.startswith("__pfx")]

    @cached_property
    def funcs_local(self) -> "pd.DataFrame":
        return self.funcs[self.funcs["bind"] == "STB_LOCAL"]

    @cached_property
    def funcs_nonlocal(self) -> "pd.DataFrame":
        # STB_GLOBAL and STB_WEAK
        return self.funcs[self.funcs["bind"] != "STB_LOCAL"]

    @cached_property
    def funcs_renamed(self) -> "pd.DataFrame":
        res = self.funcs[self.funcs["name"].str.contains(r"\.")]
        assert (res["bind"] == "STB_LOCAL").all()
        return res

    def _repr_html_(self):
        return self.data._repr_html_()
