from pathlib import Path

UTILS_PATH = Path(__file__).parent
PROJ_PATH = UTILS_PATH.parent

DATA_PATH = PROJ_PATH / "data"
OUTPUT_PATH = PROJ_PATH / "output"

PAPER_PATH = PROJ_PATH / "paper"
TAB_PATH = PAPER_PATH / "tabs"
FIG_PATH = PAPER_PATH / "figs"

SOFTWARE_PATH = PROJ_PATH / "software"

BCC_PATH = SOFTWARE_PATH / "bcc"
BCC_TOOLS_PATH = BCC_PATH / "libbpf-tools"
BCC_OBJ_PATH = BCC_TOOLS_PATH / ".output"

TRACEE_PATH = SOFTWARE_PATH / "tracee"

FONTS_PATH = UTILS_PATH / "fonts"
FONT_MONO = FONTS_PATH / "Inconsolata_ExtraCondensed-Medium.ttf"
