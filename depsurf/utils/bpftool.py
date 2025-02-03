from pathlib import Path
from functools import partial

from .decorator import check_result_path
from .system import system


PROJ_PATH = Path(__file__).parent.parent.parent
BPFTOOL_SRC_PATH = PROJ_PATH / "third_party" / "bpftool" / "src"
BPFTOOL_PATCH_PATH = PROJ_PATH / "third_party" / "bpftool.patch"
BPFTOOL_BIN_PATH = BPFTOOL_SRC_PATH / "bpftool"


@check_result_path
def dump_raw_btf_impl(raw_btf_path: Path, cmd: str, result_path: Path):
    system(f"{BPFTOOL_BIN_PATH} btf dump file {raw_btf_path} {cmd} > {result_path}")


@check_result_path
def gen_min_btf(obj_file, result_path, debug=False):
    debug_arg = "-d" if debug else ""
    system(
        f"{BPFTOOL_BIN_PATH} {debug_arg} gen min_core_btf {obj_file} {result_path} {obj_file}"
    )


dump_raw_btf_header = partial(dump_raw_btf_impl, cmd="format c")
dump_raw_btf_txt = partial(dump_raw_btf_impl, cmd="format raw")
dump_raw_btf_json = partial(dump_raw_btf_impl, cmd="--json")
