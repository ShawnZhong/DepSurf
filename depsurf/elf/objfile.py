import logging
from functools import cached_property
from pathlib import Path

from depsurf.utils import check_result_path, system, get_cstr
from elftools.elf.elffile import ELFFile


from .symtab import SymbolInfo
from .sections import Sections


class ObjectFile:
    def __init__(self, path: Path):
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
    def sections(self) -> Sections:
        return Sections(self.elffile)

    def addr_to_offset(self, addr):
        offsets = list(self.elffile.address_offsets(addr))
        if len(offsets) == 1:
            return offsets[0]
        elif len(offsets) == 0:
            raise ValueError(f"Address {addr:x} not found")
        else:
            raise ValueError(f"Multiple offsets found for address {addr:x}")

    def get_bytes(self, addr, size=8) -> bytes:
        offset = self.addr_to_offset(addr)
        self.file.seek(offset)
        return self.file.read(size)

    def get_int(self, addr, size) -> int:
        b = self.get_bytes(addr, size)
        return int.from_bytes(b, self.byteorder)

    def get_cstr(self, addr, size=512) -> str:
        data = self.get_bytes(addr, size)
        return get_cstr(data, 0)

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
    with open(vmlinux_path, "rb") as f:
        elf = ELFFile(f)

        if elf.has_dwarf_info():
            # Ref: https://github.com/torvalds/linux/blob/master/scripts/Makefile.btf
            system(
                f"pahole "
                # f"--btf_gen_floats "
                f"--lang_exclude=rust "
                # f"--btf_gen_optimized "
                f"--btf_encode_detached {result_path} "
                f"{vmlinux_path}"
            )
            return

        btf = elf.get_section_by_name(".BTF")
        if btf:
            logging.info(f"Extracting .BTF from {vmlinux_path} to {result_path}")
            with open(result_path, "wb") as f:
                f.write(btf.data())
            # system(
            #     f"objcopy -I elf64-little {self.path} --dump-section .BTF={btf_path}"
            # )
            return

        raise ValueError(f"No BTF or DWARF in {vmlinux_path}")
