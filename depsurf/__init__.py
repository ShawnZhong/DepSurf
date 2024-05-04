import logging

from .bpf import *
from .btf import *
from .deps import *
from .diff import *
from .dwarf import *
from .elf import *
from .linux import *
from .paths import *
from .prep import *
from .utils import *
from .version import *

logging.basicConfig(
    level=logging.INFO,
    format="[%(filename)12s:%(lineno)-3d] %(levelname)s: %(message)s",
)
