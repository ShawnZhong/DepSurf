import logging
from pathlib import Path

from elftools.elf.elffile import ELFFile

from depsurf.utils import manage_result_path, system


def list_deb(deb_path: Path):
    system(f"dpkg -c {deb_path}")


@manage_result_path
def extract_deb(deb_path: Path, file_path: str, result_path: Path):
    logging.info(f"Extracting {file_path} in {deb_path} to {result_path}")
    # system(f"dpkg -x {deb_path} {tmp_path}")
    system(f"dpkg --fsys-tarfile {deb_path} | tar -xO .{file_path} > {result_path}")


@manage_result_path
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
            #     f"objcopy -I elf64-little {self.path} --dump-section .BTF={result_path}"
            # )
            return

        raise ValueError(f"No BTF or DWARF in {vmlinux_path}")
