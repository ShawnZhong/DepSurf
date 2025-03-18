import logging
import shutil
from functools import cached_property
from pathlib import Path
from typing import Dict, Literal

from elftools.elf.dynamic import DynamicSection
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

from depsurf.utils import system


def get_objdump_path():
    canidates = ["llvm-objdump-18", "llvm-objdump", "objdump"]
    for prog in canidates:
        path = shutil.which(prog)
        if path:
            return path
    else:
        raise FileNotFoundError(f"None of {canidates} found")


def objdump(path: Path):
    system(
        f"{get_objdump_path()} --disassemble --reloc --source {path}",
    )


def hexdump(path: Path):
    system(f"hexdump -C {path}")


def get_cstr(data: bytes, off: int) -> str:
    end = data.find(b"\x00", off)
    return data[off:end].decode()


class FileBytes:
    def __init__(self, vmlinux_path: Path):
        self.file = open(vmlinux_path, "rb")
        self.elf = ELFFile(self.file)
        self.stream = self.elf.stream
        self.ptr_size = self.elf.elfclass // 8
        self.byteorder: Literal["little", "big"] = (
            "little" if self.elf.little_endian else "big"
        )

    def __del__(self):
        self.file.close()

    def addr_to_offset(self, addr):
        offsets = list(self.elf.address_offsets(addr))
        if len(offsets) == 1:
            return offsets[0]
        elif len(offsets) == 0:
            raise ValueError(f"Address {addr:x} not found")
        else:
            raise ValueError(f"Multiple offsets found for address {addr:x}")

    def get_bytes(self, addr, size=8) -> bytes:
        if addr in self.relocations:
            assert size == 8
            return self.relocations[addr]
        offset = self.addr_to_offset(addr)
        self.stream.seek(offset)
        return self.stream.read(size)

    def get_int(self, addr, size) -> int:
        b = self.get_bytes(addr, size)
        return int.from_bytes(b, self.byteorder)

    def get_cstr(self, addr, size=4096) -> str:
        data = self.get_bytes(addr, size)
        return get_cstr(data, 0)

    @cached_property
    def relocations(self) -> Dict[int, bytes]:
        arch = self.elf["e_machine"]
        if arch not in ("EM_AARCH64", "EM_S390"):
            return {}

        relo_sec = self.elf.get_section_by_name(".rela.dyn")
        if not isinstance(relo_sec, RelocationSection):
            logging.warning("No .rela.dyn found")
            return {}

        if arch == "EM_S390":
            dynsym = self.elf.get_section_by_name(".dynsym")
            if not isinstance(dynsym, DynamicSection):
                logging.warning("No .dynsym found")
                return {}

        constant = 1 << self.elf.elfclass

        result = {}
        for r in relo_sec.iter_relocations():
            info_type = r["r_info_type"]
            if info_type == 0:
                continue
            elif arch == "EM_AARCH64":
                # Ref: https://github.com/torvalds/linux/blob/a2c63a3f3d687ac4f63bf4ffa04d7458a2db350b/arch/arm64/kernel/pi/relocate.c#L19-L23
                if info_type != 1027:  # R_AARCH64_RELATIVE
                    continue
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
                raise ValueError(f"Unknown relocation type {r} for arch {arch}")
            addr = r["r_offset"]
            result[addr] = val.to_bytes(8, self.byteorder)

        return result
