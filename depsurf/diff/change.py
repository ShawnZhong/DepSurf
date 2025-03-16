import dataclasses
from dataclasses import dataclass
from typing import Dict

from depsurf.issues import IssueEnum


class BaseChange:
    issue_map = {}
    issue: IssueEnum

    def __init_subclass__(cls):
        cls.issue_map[cls.issue] = cls

    @classmethod
    def from_dict(cls, data: Dict):
        return cls.issue_map[data["issue"]](**data)

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


#######################
# Struct changes
#######################
# @dataclass
# class StructLayoutChange(BaseChange):
#     issue: IssueEnum = IssueEnum.STRUCT_LAYOUT


@dataclass
class FieldAdd(BaseChange):
    name: str
    type: dict
    issue: IssueEnum = IssueEnum.FIELD_ADD


@dataclass
class FieldRemove(BaseChange):
    name: str
    type: dict
    issue: IssueEnum = IssueEnum.FIELD_REMOVE


@dataclass
class FieldType(BaseChange):
    name: str
    old: dict
    new: dict
    issue: IssueEnum = IssueEnum.FIELD_TYPE


#######################
# Function changes
#######################
@dataclass
class FuncReturn(BaseChange):
    old: str
    new: str
    issue: IssueEnum = IssueEnum.RETURN_TYPE


@dataclass
class ParamRemove(BaseChange):
    name: str
    type: dict
    issue: IssueEnum = IssueEnum.PARAM_REMOVE


@dataclass
class ParamAdd(BaseChange):
    name: str
    type: dict
    issue: IssueEnum = IssueEnum.PARAM_ADD


@dataclass
class ParamReorder(BaseChange):
    old: dict
    new: dict
    issue: IssueEnum = IssueEnum.PARAM_REORDER


@dataclass
class ParamType(BaseChange):
    name: str
    old: dict
    new: dict
    issue: IssueEnum = IssueEnum.PARAM_TYPE


#######################
# Tracepoint changes
#######################
@dataclass
class TraceEventChange(BaseChange):
    issue: IssueEnum = IssueEnum.TRACE_EVENT_CHANGE


@dataclass
class TraceFuncChange(BaseChange):
    issue: IssueEnum = IssueEnum.TRACE_FUNC_CHANGE


@dataclass
class TraceFormatChange(BaseChange):
    old: str
    new: str
    issue: IssueEnum = IssueEnum.TRACE_FMT_CHANGE

    def format(self):
        return f"\n{self.old}\n{self.new}"


#######################
# Enum changes
#######################
@dataclass
class EnumValAdd(BaseChange):
    name: str
    val: int
    issue: IssueEnum = IssueEnum.VAL_ADD


@dataclass
class EnumValRemove(BaseChange):
    name: str
    val: int
    issue: IssueEnum = IssueEnum.VAL_REMOVE


@dataclass
class EnumValChange(BaseChange):
    name: str
    old_val: int
    new_val: int
    issue: IssueEnum = IssueEnum.VAL_CHANGE


#######################
# Config changes
#######################
@dataclass
class ConfigChange(BaseChange):
    old: str
    new: str
    issue: IssueEnum = IssueEnum.CONFIG_CHANGE
