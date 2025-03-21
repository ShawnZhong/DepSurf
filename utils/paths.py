from pathlib import Path

UTILS_PATH = Path(__file__).parent
PROJ_PATH = UTILS_PATH.parent

DATA_PATH = PROJ_PATH / "data"
OUTPUT_PATH = DATA_PATH / "output"

PAPER_PATH = PROJ_PATH / "paper"
TAB_PATH = PAPER_PATH / "tabs"
FIG_PATH = PAPER_PATH / "figs"

SOFTWARE_PATH = DATA_PATH / "software"

FONTS_PATH = UTILS_PATH / "fonts"
FONT_MONO = FONTS_PATH / "Inconsolata_ExtraCondensed-Medium.ttf"
