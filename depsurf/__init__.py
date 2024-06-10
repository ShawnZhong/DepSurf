import logging

from .bpf import *
from .btf import *
from .dep import *
from .diff import *
from .funcs import *
from .image import *
from .image_pair import *
from .linux import *
from .paths import *
from .prep import *
from .report import *
from .utils import *
from .version import *
from .versions import *

logging.basicConfig(
    level=logging.INFO,
    format="[%(filename)16s:%(lineno)-3d] %(levelname)s: %(message)s",
)
