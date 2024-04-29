from pathlib import Path
from functools import partial

from depsurf.utils import system, check_result_path


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


@check_result_path
def dump_btf_impl(btf_path: Path, cmd: str, result_path: Path):
    system(f"{get_bpftool_path()} btf dump file {btf_path} {cmd} > {result_path}")


dump_btf_header = partial(dump_btf_impl, cmd="format c")
dump_btf_txt = partial(dump_btf_impl, cmd="format raw")
dump_btf_json = partial(dump_btf_impl, cmd="--json")
