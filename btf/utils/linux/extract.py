from pathlib import Path


def extract_vmlinuz_files(deb_paths, result_path):
    from ..system import system

    result_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, deb_path in deb_paths.items():
        vmlinuz_path = result_path / f"{name}.vmlinuz"
        if not vmlinuz_path.exists():
            print(f"Extracting {deb_path} to {vmlinuz_path}")
            # system(f"dpkg -x {deb_path} {tmp_path}")
            system(
                f"dpkg --fsys-tarfile {deb_path} | tar -xO ./boot/vmlinuz-{name} > {vmlinuz_path}"
            )
        else:
            print(f"Using {vmlinuz_path}")
        results[name] = vmlinuz_path
    return results


def extract_vmlinux_files(vmlinuz_paths, result_path):
    from vmlinux_to_elf.vmlinuz_decompressor import obtain_raw_kernel_from_file

    result_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, vmlinuz_path in vmlinuz_paths.items():
        vmlinux_path = result_path / f"{name}.vmlinux"
        if not vmlinux_path.exists():
            print(f"Extracting {vmlinuz_path} to {vmlinux_path}")
            # system(f"zcat {vmlinuz_path} > {vmlinux_path}")
            # system(f"extract-vmlinux {vmlinuz_path} > {vmlinux_path}")
            with open(vmlinuz_path, "rb") as fin, open(vmlinux_path, "wb") as fout:
                fout.write(obtain_raw_kernel_from_file(fin.read()))
            if vmlinux_path.stat().st_size == 0:
                print(f"Failing to extract {vmlinuz_path} to {vmlinux_path}")
                vmlinux_path.unlink()
        else:
            print(f"Using {vmlinux_path}")
        results[name] = vmlinux_path
    return results


def extract_btf_files(vmlinux_paths, result_path):
    from elftools.elf.elffile import ELFFile

    results = {}
    for name, vmlinux_path in vmlinux_paths.items():
        with open(vmlinux_path, "rb") as f:
            elf = ELFFile(f)
            btf = elf.get_section_by_name(".BTF")
            if not btf:
                print(f"No .BTF section in {vmlinux_path}")
                continue
            btf_path = result_path / f"{name}.btf"
            if btf_path.exists() and btf_path.stat().st_size == btf.data_size:
                print(f"Using {btf_path}")
            else:
                print(f"Extracting BTF from {vmlinux_path} to {btf_path}")
                with open(btf_path, "wb") as f:
                    f.write(btf.data())
                # system(
                #     f"objcopy -I elf64-little {vmlinux_path} --dump-section .BTF={btf_path}"
                # )
                # we use objcopy instead of pahole because pahole sometimes fails with
                # "btf_encoder__new: cannot get ELF header", and pahole seems does more
                # processing than we need
                # system(f"pahole --btf_encode_detached {btf_path} {vmlinux_path}")
        results[name] = btf_path

    return results
