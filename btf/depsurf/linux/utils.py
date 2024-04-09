import logging
from pathlib import Path

from depsurf.utils import system, check_result_path


@check_result_path
def download(url: str, result_path: Path):
    import urllib.request

    logging.info(f"Downloading {url} to {result_path}")
    urllib.request.urlretrieve(url, result_path)


@check_result_path
def unzip_gz(gz_path: Path, result_path: Path):
    import gzip

    logging.info(f"Unzipping {gz_path} to {result_path}")
    with gzip.open(gz_path, "rb") as f_in:
        with open(result_path, "wb") as f_out:
            f_out.write(f_in.read())


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

        btf = elf.get_section_by_name(".BTF")
        if btf:
            logging.info(f"Extracting .BTF from {vmlinux_path} to {result_path}")
            with open(result_path, "wb") as f:
                f.write(btf.data())
            # system(
            #     f"objcopy -I elf64-little {vmlinux_path} --dump-section .BTF={btf_path}"
            # )
            return

        if elf.has_dwarf_info():
            system(f"pahole --btf_encode_detached {result_path} {vmlinux_path}")
            return

        logging.warning(f"No BTF or DWARF in {vmlinux_path}")


@check_result_path
def extract_vmlinux(vmlinuz_path: Path, result_path: Path):
    from vmlinux_to_elf.vmlinuz_decompressor import obtain_raw_kernel_from_file

    logging.info(f"Extracting {vmlinuz_path} to {result_path}")
    # system(f"zcat {vmlinuz_path} > {vmlinux_path}")
    # system(f"extract-vmlinux {vmlinuz_path} > {vmlinux_path}")
    with open(vmlinuz_path, "rb") as fin, open(result_path, "wb") as fout:
        fout.write(obtain_raw_kernel_from_file(fin.read()))
    if result_path.stat().st_size == 0:
        logging.warning(f"Failing to extract {vmlinuz_path} to {result_path}")
        result_path.unlink()
