from elftools.elf.elffile import ELFFile
from depsurf.utils import system


class DWARF:
    def __init__(self, elffile: ELFFile):
        self.dwarfinfo = elffile.get_dwarf_info(relocate_dwarf_sections=False)

    @property
    def main_cu(self):
        return next(
            cu
            for cu in self.dwarfinfo.iter_CUs()
            if cu.get_top_DIE().get_full_path().endswith("main.c")
        )

    @property
    def producer(self):
        return self.main_cu.get_top_DIE().attributes["DW_AT_producer"].value.decode()

    @property
    def flags(self):
        return self.producer.split(" ")[3:]
