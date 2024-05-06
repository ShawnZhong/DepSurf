import logging

from elftools.elf.dynamic import DynamicSection
from elftools.elf.relocation import RelocationSection
from elftools.elf.elffile import ELFFile


def get_relocation(elffile: ELFFile) -> dict[int, bytes]:
    byteorder = "little" if elffile.little_endian else "big"

    arch = elffile["e_machine"]
    if arch not in ("EM_AARCH64", "EM_S390"):
        return {}

    relo_sec: RelocationSection = elffile.get_section_by_name(".rela.dyn")
    if not relo_sec:
        logging.warning("No .rela.dyn found")
        return {}

    if arch == "EM_S390":
        dynsym: DynamicSection = elffile.get_section_by_name(".dynsym")
        if not dynsym:
            logging.warning("No .dynsym found")
            return {}

    constant = 1 << elffile.elfclass

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
        result[addr] = val.to_bytes(8, byteorder)

    return result
