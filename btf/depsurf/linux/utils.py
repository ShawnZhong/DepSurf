import logging

from depsurf.utils import system


def download(url, result_path, overwrite):
    result_path.parent.mkdir(parents=True, exist_ok=True)

    if result_path.exists() and not overwrite:
        logging.info(f"Using {result_path}")
        return

    import urllib.request

    logging.info(f"Downloading {url} to {result_path}")
    urllib.request.urlretrieve(url, result_path)


def unzip_gz(gz_path, result_path, overwrite):
    result_path.parent.mkdir(parents=True, exist_ok=True)

    if result_path.exists() and not overwrite:
        logging.info(f"Using {result_path}")
        return

    import gzip

    logging.info(f"Unzipping {gz_path} to {result_path}")
    with gzip.open(gz_path, "rb") as f_in:
        with open(result_path, "wb") as f_out:
            f_out.write(f_in.read())


def extract_deb(deb_path, file_path, result_path, overwrite=False):
    result_path.parent.mkdir(parents=True, exist_ok=True)

    if result_path.exists() and not overwrite:
        logging.info(f"Using {result_path}")
        return

    logging.info(f"Extracting {deb_path} to {result_path}")
    # system(f"dpkg -x {deb_path} {tmp_path}")
    system(f"dpkg --fsys-tarfile {deb_path} | tar -xO {file_path} > {result_path}")


def extract_btf(vmlinux_path, btf_path, overwrite=False):
    btf_path.parent.mkdir(parents=True, exist_ok=True)

    if btf_path.exists() and not overwrite:
        logging.info(f"Using {btf_path}")
        return

    from elftools.elf.elffile import ELFFile

    with open(vmlinux_path, "rb") as f:
        elf = ELFFile(f)

        btf = elf.get_section_by_name(".BTF")
        if btf:
            logging.info(f"Extracting .BTF from {vmlinux_path} to {btf_path}")
            with open(btf_path, "wb") as f:
                f.write(btf.data())
            # system(
            #     f"objcopy -I elf64-little {vmlinux_path} --dump-section .BTF={btf_path}"
            # )
            return

        if elf.has_dwarf_info():
            system(f"pahole --btf_encode_detached {btf_path} {vmlinux_path}")
            return

        logging.warning(f"No BTF or DWARF in {vmlinux_path}")
