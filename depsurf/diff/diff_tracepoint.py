from typing import List

from depsurf.linux import TracepointInfo

from .change import (
    BaseChange,
    TraceEventChange,
    TraceFormatChange,
    TraceFuncChange,
)
from .diff_func import diff_func
from .diff_struct import diff_struct


def diff_tracepoint(old: TracepointInfo, new: TracepointInfo) -> List[BaseChange]:
    result = []

    result_struct = diff_struct(old.struct, new.struct)
    # result_struct = [r for r in result_struct if r.issue != IssueEnum.STRUCT_LAYOUT]
    if result_struct:
        result.append(TraceEventChange())
    for r in result_struct:
        result.append(r)

    result_func = diff_func(old.func, new.func)
    if result_func:
        result.append(TraceFuncChange())
    for r in result_func:
        result.append(r)

    # if old.fmt_str != new.fmt_str:
    #     result.append(TraceFormatChange(old.fmt_str, new.fmt_str))

    return result
