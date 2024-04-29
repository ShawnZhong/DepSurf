from pathlib import Path

PROJ_PATH = Path(__file__).parent.parent

DATA_PATH = PROJ_PATH / "data"
assert DATA_PATH.exists(), f"{DATA_PATH} does not exist"

OUTPUT_PATH = PROJ_PATH / "output"
assert OUTPUT_PATH.exists(), f"{OUTPUT_PATH} does not exist"

BCC_PATH = PROJ_PATH / "csrc" / "bcc"
assert BCC_PATH.exists(), f"{BCC_PATH} does not exist"

BCC_OBJ_PATH = BCC_PATH / "libbpf-tools" / ".output"

FIG_PATH = PROJ_PATH / "paper" / "figs"
