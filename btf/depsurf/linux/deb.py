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
