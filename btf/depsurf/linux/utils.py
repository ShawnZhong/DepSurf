import logging

from depsurf.utils import system


def download(url, path, overwrite):
    if not path.exists() or overwrite:
        import urllib.request

        logging.info(f"Downloading {url} to {path}")
        urllib.request.urlretrieve(url, path)
    else:
        logging.info(f"Using {path}")


def unzip_gz(gz_path, result_path, overwrite):
    if not result_path.exists() or overwrite:
        import gzip

        logging.info(f"Unzipping {gz_path} to {result_path}")
        with gzip.open(gz_path, "rb") as f_in:
            with open(result_path, "wb") as f_out:
                f_out.write(f_in.read())
    else:
        logging.info(f"Using {result_path}")


def extract_deb(deb_path, file_path, result_path):
    if not result_path.exists():
        logging.info(f"Extracting {deb_path} to {result_path}")
        # system(f"dpkg -x {deb_path} {tmp_path}")
        system(f"dpkg --fsys-tarfile {deb_path} | tar -xO {file_path} > {result_path}")
    else:
        logging.info(f"Using {result_path}")
