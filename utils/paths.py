from pathlib import Path

UTILS_PATH = Path(__file__).parent
PROJ_PATH = UTILS_PATH.parent

OUTPUT_PATH = PROJ_PATH / "output"
REPORT_PATH = OUTPUT_PATH / "report"

OUTPUT_PATH.mkdir(exist_ok=True, parents=True)
REPORT_PATH.mkdir(exist_ok=True, parents=True)

PAPER_PATH = PROJ_PATH / "paper"
if not PAPER_PATH.exists():
    PAPER_PATH = OUTPUT_PATH
TAB_PATH = PAPER_PATH / "tabs"
FIG_PATH = PAPER_PATH / "figs"

BCC_PATH = PROJ_PATH / "csrc" / "bcc"
BCC_OBJ_PATH = BCC_PATH / "libbpf-tools" / ".output"


def iter_bcc_objects():
    if not BCC_PATH.exists():
        raise FileNotFoundError(f"{BCC_PATH} does not exist")
    if not BCC_OBJ_PATH.exists():
        raise FileNotFoundError(f"{BCC_OBJ_PATH} does not exist")
    for obj in BCC_OBJ_PATH.glob("*.bpf.o"):
        yield obj


FONTS_PATH = UTILS_PATH / "fonts"
FONT_MONO = FONTS_PATH / "Inconsolata_ExtraCondensed-Medium.ttf"
