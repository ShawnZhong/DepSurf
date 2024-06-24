from pathlib import Path
from functools import partial

from .decorator import check_result_path
from .system import system


PROJ_PATH = Path(__file__).parent.parent.parent
BPFTOOL_SRC_PATH = PROJ_PATH / "csrc" / "bpftool" / "src"
BPFTOOL_EXE_PATH = BPFTOOL_SRC_PATH / "bpftool"


@check_result_path
def dump_btf_impl(btf_path: Path, cmd: str, result_path: Path):
    system(f"{BPFTOOL_EXE_PATH} btf dump file {btf_path} {cmd} > {result_path}")


@check_result_path
def gen_min_btf(obj_file, result_path, debug=False):
    debug_arg = "-d" if debug else ""
    system(
        f"{BPFTOOL_EXE_PATH} {debug_arg} gen min_core_btf {obj_file} {result_path} {obj_file}"
    )


dump_btf_header = partial(dump_btf_impl, cmd="format c")
dump_btf_txt = partial(dump_btf_impl, cmd="format raw")
dump_btf_json = partial(dump_btf_impl, cmd="--json")


# def get_linux_tools_path():
#     parent = Path("/usr/lib/linux-tools")
#     versions = [x for x in parent.iterdir() if x.is_dir()]
#     if len(versions) == 0:
#         raise Exception("No linux-tools found")
#     versions.sort()
#     return parent / versions[-1]


# def get_bpftool_path():
#     bpftool_path = BPFTOOL_SRC_PATH / "bpftool"
#     if bpftool_path.exists():
#         return bpftool_path

#     path = get_linux_tools_path() / "bpftool"
#     if not path.exists():
#         raise Exception("bpftool not found")
#     return path
