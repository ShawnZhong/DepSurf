from typing import List

from depsurf.diff import BaseChange

from .diff_func import diff_func
from .diff_struct import diff_struct

from depsurf.linux import TracepointInfo
from depsurf.issues import IssueEnum

from dataclasses import dataclass


@dataclass
class TraceEventChange(BaseChange, enum=IssueEnum.TRACE_EVENT_CHANGE):
    pass


@dataclass
class TraceFuncChange(BaseChange, enum=IssueEnum.TRACE_FUNC_CHANGE):
    pass


def diff_tracepoint(old: TracepointInfo, new: TracepointInfo) -> List[BaseChange]:

    result_struct = diff_struct(old.struct, new.struct)
    result_func = diff_func(old.func, new.func)

    result = []
    if result_struct:
        result.append(TraceEventChange())
    for r in result_struct:
        result.append(r)
    if result_func:
        result.append(TraceFuncChange())
    for r in result_func:
        result.append(r)

    return result


def diff_nop(old, new):
    return []


@dataclass
class ConfigChange(BaseChange, enum=IssueEnum.CONFIG_CHANGE):
    old: str
    new: str

    def format(self):
        return f"{self.old} -> {self.new}"


def diff_config(old, new):
    if old != new:
        return [ConfigChange(old, new)]
    return []
