def download_package_index(package_url, download_path):
    import urllib.request
    import gzip

    gz_path = download_path / "Packages.gz"

    if not gz_path.exists():
        print(f"Downloading {package_url} to {gz_path}")
        urllib.request.urlretrieve(package_url, gz_path)
    else:
        print(f"Using {gz_path}")

    package_path = gz_path.with_suffix("")
    if not package_path.with_suffix("").exists():
        print(f"Unzipping {gz_path} to {package_path}")
        with gzip.open(gz_path, "rb") as f_in:
            with open(package_path, "wb") as f_out:
                f_out.write(f_in.read())
    else:
        print(f"Using {package_path}")

    return package_path


def parse_package_index(package_path):
    result = {}
    with open(package_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            key, val = line.split(": ", 1)
            if key == "Package":
                package = val
            elif key == "Filename":
                result[package] = val
    return result


def filter_linux_images(package_index):
    import re
    from collections import defaultdict

    result = defaultdict(dict)
    for package, path in package_index.items():
        groups = re.match(r"^linux-image-(\d+\.\d+\.\d+)-(\d+)-generic$", package)
        if groups is None:
            continue

        version, build = groups.groups()
        result[version][int(build)] = package, path

    return [v[max(v.keys())] for v in result.values()]


def download_deb_files(linux_versions, url_prefix, download_path):
    import urllib.request

    results = {}
    for package, path in linux_versions:
        url = f"{url_prefix}/{path}"
        file_path = download_path / path.split("/")[-1]
        if not file_path.exists():
            print(f"Downloading {url} to {file_path}")
            urllib.request.urlretrieve(url, file_path)
        else:
            print(f"Using {file_path}")

        key = package.removeprefix("linux-image-")
        results[key] = file_path

    return results


def extract_vmlinuz_files(deb_paths, result_path):
    from .system import system

    results = {}
    for name, deb_path in deb_paths.items():
        vmlinuz_path = result_path / f"vmlinuz-{name}"
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
    from pathlib import Path
    from .system import system

    extract_vmlinux = Path("data") / "extract-vmlinux"

    assert extract_vmlinux.exists(), f"{extract_vmlinux} does not exist"

    results = {}
    for name, vmlinuz_path in vmlinuz_paths.items():
        vmlinux_path = result_path / f"vmlinux-{name}"
        if not vmlinux_path.exists() or vmlinux_path.stat().st_size == 0:
            print(f"Extracting {vmlinuz_path} to {vmlinux_path}")
            # TODO: check how the file is compressed
            if "arm64" in str(vmlinuz_path):
                system(f"zcat {vmlinuz_path} > {vmlinux_path}")
            else:
                system(f"{extract_vmlinux} {vmlinuz_path} > {vmlinux_path}")
        else:
            print(f"Using {vmlinux_path}")
        results[name] = vmlinux_path
    return results


def extract_btf_files(vmlinux_paths, result_path):
    from .linux_version import get_linux_version_tuple
    from .system import system

    results = {}
    for name, vmlinux_path in vmlinux_paths.items():
        # if get_linux_version_tuple(name) <= (5, 8, 0):
        # print(f"Skipping {name} because it doesn't have BTF support")
        # continue
        btf_path = result_path / f"{name}.btf"
        if not btf_path.exists():
            print(f"Extracting {vmlinux_path} to {btf_path}")
            system(
                f"objcopy -I elf64-little {vmlinux_path} --dump-section .BTF={btf_path}"
            )
            # we use objcopy instead of pahole because pahole sometimes fails with
            # "btf_encoder__new: cannot get ELF header", and pahole seems does more
            # processing than we need
            # system(f"pahole --btf_encode_detached {btf_path} {vmlinux_path}")
        else:
            print(f"Using {btf_path}")
        results[vmlinux_path.name] = btf_path

    return results
