from pathlib import Path
from functools import partial

from depsurf.utils import system, check_result_path


PROJ_PATH = Path(__file__).parent.parent.parent


def get_linux_tools_path():
    parent = Path("/usr/lib/linux-tools")
    versions = [x for x in parent.iterdir() if x.is_dir()]
    if len(versions) == 0:
        raise Exception("No linux-tools found")
    versions.sort()
    return parent / versions[-1]


def get_bpftool_path():
    bpftool_path = PROJ_PATH / "csrc" / "bpftool" / "src" / "bpftool"
    if bpftool_path.exists():
        return bpftool_path

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
