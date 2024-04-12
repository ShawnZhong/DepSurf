import logging
from pathlib import Path

from depsurf.utils import system, check_result_path


def list_deb(deb_path: Path):
    system(f"dpkg -c {deb_path}")


@check_result_path
def extract_deb(deb_path: Path, file_path: Path, result_path: Path):
    logging.info(f"Extracting {deb_path} to {result_path}")
    # system(f"dpkg -x {deb_path} {tmp_path}")
    system(f"dpkg --fsys-tarfile {deb_path} | tar -xO {file_path} > {result_path}")


@check_result_path
def extract_btf(vmlinux_path: Path, result_path: Path):
    from elftools.elf.elffile import ELFFile

    with open(vmlinux_path, "rb") as f:
        elf = ELFFile(f)

        if elf.has_dwarf_info():
            system(f"pahole --btf_encode_detached {result_path} {vmlinux_path}")
            return

        btf = elf.get_section_by_name(".BTF")
        if btf:
            logging.info(f"Extracting .BTF from {vmlinux_path} to {result_path}")
            with open(result_path, "wb") as f:
                f.write(btf.data())
            # system(
            #     f"objcopy -I elf64-little {vmlinux_path} --dump-section .BTF={btf_path}"
            # )
            return

        raise ValueError(f"No BTF or DWARF in {vmlinux_path}")
