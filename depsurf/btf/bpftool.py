from functools import partial
from pathlib import Path

from depsurf.utils import manage_result_path, system

CURR_PATH = Path(__file__).parent
BPFTOOL_SRC_PATH = CURR_PATH / "bpftool" / "src"
BPFTOOL_PATCH_PATH = CURR_PATH / "bpftool.patch"
BPFTOOL_BIN_PATH = BPFTOOL_SRC_PATH / "bpftool"


@manage_result_path
def gen_min_btf(obj_file, result_path):
    system(
        f"{BPFTOOL_BIN_PATH} gen min_core_btf {obj_file} {result_path} {obj_file}",
        linux=True,
    )


@manage_result_path
def dump_btf(raw_btf_path: Path, cmd: str, result_path: Path):
    system(
        f"{BPFTOOL_BIN_PATH} btf dump file {raw_btf_path} {cmd} > {result_path}",
        linux=True,
    )


dump_btf_header = partial(dump_btf, cmd="format c")
dump_btf_txt = partial(dump_btf, cmd="format raw")
dump_btf_json = partial(dump_btf, cmd="--json")
