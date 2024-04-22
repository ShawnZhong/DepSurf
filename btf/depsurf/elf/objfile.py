import logging
from functools import cached_property
from pathlib import Path

from depsurf.utils import check_result_path, system
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

from .symtab import SymbolInfo
from .utils import get_cstr


class SectionInfo:
    def __init__(self, elffile: ELFFile):
        self.elffile = elffile
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
                    "addr": s.header.sh_addr,
                    # "data": s.data()[:15],
                }
                for s in elffile.iter_sections()
            ]
        ).set_index("name")
        return df

    def _repr_html_(self):
        return self.data.to_html(formatters={"addr": hex, "offset": hex, "size": hex})


class ObjectFile:
    def __init__(self, path):
        self.path = Path(path)
        self.file = open(path, "rb")
        self.elffile = ELFFile(self.file)
        self.ptr_size = self.elffile.elfclass // 8
        self.byteorder = "little" if self.elffile.little_endian else "big"

    def __del__(self):
        self.file.close()

    @cached_property
    def symtab(self) -> SymbolInfo:
        return SymbolInfo.from_elffile(self.elffile)

    @cached_property
    def sections(self) -> SectionInfo:
        return SectionInfo(self.elffile)

    @cached_property
    def relocations(self):
        arch = self.elffile["e_machine"]
        if arch not in ("EM_AARCH64", "EM_S390"):
            return {}

        from elftools.elf.dynamic import DynamicSection

        relo_sec: RelocationSection = self.elffile.get_section_by_name(".rela.dyn")
        if not relo_sec:
            logging.warning("No .rela.dyn found")
            return {}

        if arch == "EM_S390":
            dynsym: DynamicSection = self.elffile.get_section_by_name(".dynsym")
            if not dynsym:
                logging.warning("No .dynsym found")
                return {}

        constant = 1 << self.elffile.elfclass

        result = {}
        for r in relo_sec.iter_relocations():
            info_type = r["r_info_type"]
            if info_type == 0:
                continue
            elif arch == "EM_AARCH64" and info_type == 1027:
                # R_AARCH64_RELATIVE
                # Ref: https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/arm64/kernel/pi/relocate.c#L15
                val = constant + r["r_addend"]
            elif arch == "EM_S390" and info_type in (12, 22):
                # R_390_RELATIVE and R_390_64
                # Ref:
                # - https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/s390/boot/startup.c#L145
                # - https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/s390/kernel/machine_kexec_reloc.c#L5
                val = r["r_addend"]
                info = r["r_info"]
                sym_idx = info >> 32
                if sym_idx != 0:
                    sym = dynsym.get_symbol(sym_idx)
                    val += sym["st_value"]
            else:
                raise ValueError(f"Unknown relocation type {r}")
            addr = r["r_offset"]
            result[addr] = val.to_bytes(8, self.byteorder)

        return result

    def addr_to_offset(self, addr):
        offsets = list(self.elffile.address_offsets(addr))
        if len(offsets) == 1:
            return offsets[0]
        elif len(offsets) == 0:
            raise ValueError(f"Address {addr:x} not found")
        else:
            raise ValueError(f"Multiple offsets found for address {addr:x}")

    def get_bytes_fileoff(self, offset, size=8) -> bytes:
        self.file.seek(offset)
        return self.file.read(size)

    def get_bytes(self, addr, size=8) -> bytes:
        if addr in self.relocations:
            assert size == 8
            return self.relocations[addr]
        offset = self.addr_to_offset(addr)
        return self.get_bytes_fileoff(offset, size)

    def get_int(self, addr, size) -> int:
        b = self.get_bytes(addr, size)
        return int.from_bytes(b, self.byteorder)

    def get_cstr(self, addr, size=512) -> str:
        data = self.get_bytes(addr, size)
        return get_cstr(data, 0)

    def extract_btf(self, result_path: Path):
        from elftools.elf.elffile import ELFFile

        with open(self.path, "rb") as f:
            elf = ELFFile(f)

            if elf.has_dwarf_info():
                # Ref: https://github.com/torvalds/linux/blob/master/scripts/Makefile.btf
                system(
                    f"pahole "
                    # f"--btf_gen_floats "
                    f"--lang_exclude=rust "
                    # f"--btf_gen_optimized "
                    f"--btf_encode_detached {result_path} "
                    f"{self.path}"
                )
                return

            btf = elf.get_section_by_name(".BTF")
            if btf:
                logging.info(f"Extracting .BTF from {self.path} to {result_path}")
                with open(result_path, "wb") as f:
                    f.write(btf.data())
                # system(
                #     f"objcopy -I elf64-little {self.path} --dump-section .BTF={btf_path}"
                # )
                return

            raise ValueError(f"No BTF or DWARF in {self.path}")

    @staticmethod
    def get_objdump_path():
        import shutil

        canidates = ["llvm-objdump-18", "llvm-objdump", "objdump"]
        for prog in canidates:
            path = shutil.which(prog)
            if path:
                return path
        else:
            raise FileNotFoundError(f"None of {canidates} found")

    def objdump(self):
        system(
            f"{self.get_objdump_path()} --disassemble --reloc --source {self.path}",
        )

    def hexdump(self):
        system(f"hexdump -C {self.path}")


@check_result_path
def extract_btf(vmlinux_path: Path, result_path: Path):
    ObjectFile(vmlinux_path).extract_btf(result_path)
