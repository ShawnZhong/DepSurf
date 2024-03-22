import logging

from .bpftool import *
from .btf import *
from .dwarf import *
from .diff import *
from .linux import *
from .normalize import *
from .paths import *
from .score import *
from .utils import *


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
    )


setup_logging()


def setup_pandas():
    import pandas as pd

    pd.set_option("display.min_rows", 300)
    pd.set_option("display.max_rows", 300)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", 1000)


def reload_depsurf():
    import sys
    from importlib import reload

    for k in list(sys.modules.keys()):
        if k.startswith("depsurf"):
            del sys.modules[k]

    import depsurf

    reload(depsurf)
