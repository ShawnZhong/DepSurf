import logging

from .bpf_program import *
from .btf import *
from .dep import *
from .diff import *
from .funcs import *
from .issues import *
from .linux import *
from .linux_image import *
from .paths import *
from .prep import *
from .report import *
from .utils import *
from .version import *
from .version_group import *
from .version_pair import *

logging.basicConfig(
    level=logging.INFO,
    format="[%(filename)16s:%(lineno)-3d] %(levelname)s: %(message)s",
)
