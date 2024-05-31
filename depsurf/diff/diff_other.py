from .diff_func import diff_func
from .diff_struct import diff_struct

from depsurf.linux import TracepointInfo


def diff_tracepoint(old: TracepointInfo, new: TracepointInfo, assert_diff=False):
    result_struct = diff_struct(old.struct, new.struct, assert_diff)
    result_func = diff_func(old.func, new.func, assert_diff)
    return result_struct + result_func
