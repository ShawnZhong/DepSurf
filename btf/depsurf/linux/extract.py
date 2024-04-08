from .utils import extract_deb, extract_btf

import logging


def extract_vmlinuz_files(deb_paths, result_path):
    results = {}
    for name, deb_path in deb_paths.items():
        vmlinuz_path = result_path / f"{name}.vmlinuz"
        extract_deb(deb_path, f"./boot/vmlinuz-{name}", vmlinuz_path)
        results[name] = vmlinuz_path
    return results


def extract_vmlinux_files(vmlinuz_paths, result_path):
    from vmlinux_to_elf.vmlinuz_decompressor import obtain_raw_kernel_from_file

    result_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, vmlinuz_path in vmlinuz_paths.items():
        vmlinux_path = result_path / f"{name}.vmlinux"
        if not vmlinux_path.exists():
            logging.info(f"Extracting {vmlinuz_path} to {vmlinux_path}")
            # system(f"zcat {vmlinuz_path} > {vmlinux_path}")
            # system(f"extract-vmlinux {vmlinuz_path} > {vmlinux_path}")
            with open(vmlinuz_path, "rb") as fin, open(vmlinux_path, "wb") as fout:
                fout.write(obtain_raw_kernel_from_file(fin.read()))
            if vmlinux_path.stat().st_size == 0:
                logging.warning(f"Failing to extract {vmlinuz_path} to {vmlinux_path}")
                vmlinux_path.unlink()
        else:
            logging.info(f"Using {vmlinux_path}")
        results[name] = vmlinux_path
    return results


def extract_btf_files(vmlinux_paths, result_path):
    results = {}
    for name, vmlinux_path in vmlinux_paths.items():
        btf_path = result_path / f"{name}.btf"
        extract_btf(vmlinux_path, btf_path)
        results[name] = btf_path

    return results
