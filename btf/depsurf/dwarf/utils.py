from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile


def disable_dwarf_cache():
    from elftools.dwarf.dwarfinfo import CompileUnit

    def _get_cached_DIE(self: CompileUnit, offset):
        top_die_stream = self.get_top_DIE().stream
        return DIE(cu=self, stream=top_die_stream, offset=offset)

    CompileUnit._get_cached_DIE = _get_cached_DIE


def arg_elf_or_path(func):
    def wrapper(file, *args, **kwargs):
        if isinstance(file, str):
            with open(file, "rb") as f:
                elffile = ELFFile(f)
                return func(elffile, *args, **kwargs)
        elif isinstance(file, ELFFile):
            return func(file, *args, **kwargs)
        else:
            raise ValueError(f"Invalid file type: {type(file)}")

    return wrapper


@arg_elf_or_path
def get_symbol_info_impl(elffile: ELFFile):
    import pandas as pd

    symtab = elffile.get_section_by_name(".0")
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
                "size": sym.entry.st_size,
                # **{k: v for k, v in sym.entry.items() if k not in ("st_info", "st_other", "st_name", "st_shndx")},
            }
            for sym in symtab.iter_symbols()
        ]
    )

    if (df["local"] == 0).all():
        df = df.drop(columns=["local"])

    return df


@arg_elf_or_path
def get_section_info_impl(elffile: ELFFile):
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "name": s.name,
                **{k: v for k, v in s.header.items() if k != "sh_name"},
                "data": s.data()[:15],
            }
            for s in elffile.iter_sections()
        ]
    )
    return df
