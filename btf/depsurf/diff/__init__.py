from enum import Enum

from ..btf import Kind
from .struct import diff_struct, StructChange
from .func import diff_func, FuncChange
from .enum import diff_enum, EnumChange
from .impl import check_diff_impl


class Consequence(str, Enum):
    COMPILER = "Compiler"
    RUNTIME = "Runtime"
    SLIENT = "Silent"
    CORE = "CO-RE"

    @property
    def weight(self):
        return {
            self.COMPILER: 1,
            self.RUNTIME: 2,
            self.SLIENT: 7,
            self.CORE: 0,
        }[self]


def get_diff_fn(kind):
    return {
        Kind.STRUCT: diff_struct,
        Kind.UNION: diff_struct,
        Kind.FUNC: diff_func,
        Kind.ENUM: diff_enum,
    }[kind]


def get_reason_enum(kind):
    return {
        Kind.STRUCT: StructChange,
        Kind.UNION: StructChange,
        Kind.FUNC: FuncChange,
        Kind.ENUM: EnumChange,
    }[kind]


def check_diff(dict1, dict2, kind):
    diff_fn = get_diff_fn(kind)
    reason_enum = get_reason_enum(kind)
    return check_diff_impl(dict1, dict2, kind, diff_fn, reason_enum)
