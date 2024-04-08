import logging
from pathlib import Path
from typing import Tuple, Optional

from depsurf.utils import system


def get_linux_tools_path():
    parent = Path("/usr/lib/linux-tools")
    versions = [x for x in parent.iterdir() if x.is_dir()]
    if len(versions) == 0:
        raise Exception("No linux-tools found")
    versions.sort()
    return parent / versions[-1]


def get_bpftool_path():
    # return "/Users/szhong/Downloads/bpf-study/bcc/libbpf-tools/bpftool/src/bpftool"
    path = get_linux_tools_path() / "bpftool"
    if not path.exists():
        raise Exception("bpftool not found")
    return path


def gen_min_btf(obj_file, overwrite=False):
    btf_file = obj_file.with_suffix(".min.btf")
    if btf_file.exists() and not overwrite:
        logging.info(f"{btf_file} already exists")
        return btf_file

    kernel_btf = "/sys/kernel/btf/vmlinux"
    system(
        f"{get_bpftool_path()} -d gen min_core_btf {kernel_btf} {btf_file} {obj_file}"
    )
    return btf_file


def dump_btf(
    btf_path: Path, overwrite: bool, result_paths: Optional[Tuple[Path]] = None
):
    cmd_map = {
        ".h": "format c",
        ".txt": "format raw",
        ".json": "--json",
    }

    if result_paths is None:
        result_paths = (btf_path.with_suffix(suffix) for suffix in cmd_map.keys())

    for result_path in result_paths:
        cmd = cmd_map.get(result_path.suffix)
        assert cmd is not None, f"Unknown suffix: {result_path.suffix}"

        if result_path.exists() and not overwrite:
            logging.info(f"Using {result_path}")
            continue

        system(f"{get_bpftool_path()} btf dump file {btf_path} {cmd} > {result_path}")
