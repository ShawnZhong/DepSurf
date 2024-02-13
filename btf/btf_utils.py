from enum import Enum
from pathlib import Path


class Kind(str, Enum):
    INT = "INT"
    PTR = "PTR"
    ARRAY = "ARRAY"
    STRUCT = "STRUCT"
    UNION = "UNION"
    ENUM = "ENUM"
    FWD = "FWD"
    TYPEDEF = "TYPEDEF"
    VOLATILE = "VOLATILE"
    CONST = "CONST"
    RESTRICT = "RESTRICT"
    FUNC = "FUNC"
    FUNC_PROTO = "FUNC_PROTO"
    VAR = "VAR"
    DATASEC = "DATASEC"
    FLOAT = "FLOAT"
    DECL_TAG = "DECL_TAG"
    TYPE_TAG = "TYPE_TAG"
    ENUM64 = "ENUM64"


def get_linux_tools_path():
    parent = Path("/usr/lib/linux-tools")
    versions = [x for x in parent.iterdir() if x.is_dir()]
    if len(versions) == 0:
        raise Exception("No linux-tools found")
    versions.sort()
    return parent / versions[-1]


def get_bpftool_path():
    path = get_linux_tools_path() / "bpftool"
    if not path.exists():
        raise Exception("bpftool not found")
    return path
