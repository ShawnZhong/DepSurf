from enum import StrEnum


class Consequence(StrEnum):
    # Rank by severity, don't change the order
    MISS = "Missing invocation"
    STRAY = "Stray read"
    ERROR = "Error"
    OK = "OK"
    UNKNOWN = "Unknown"


class IssueEnum(StrEnum):
    # Not really an issue, defined for convenience
    OLD = "Old"
    NEW = "New"

    # Generic status
    OK = "OK"
    ABSENT = "Absent"

    # Generic changes
    ADD = "Added"
    REMOVE = "Removed"
    CHANGE = "Changed"
    NO_CHANGE = "No change"
    BOTH_ABSENT = "Both absent"

    # Function status
    SELECTIVE_INLINE = "Selective Inline"
    FULL_INLINE = "Full Inline"
    TRANSFORMATION = "Transformation"
    DUPLICATE = "Duplicate"
    COLLISION = "Collision"

    # Function changes
    FUNC_ADD = "Function added"
    FUNC_REMOVE = "Function removed"
    FUNC_CHANGE = "Function changed"
    PARAM_ADD = "Param added"
    PARAM_REMOVE = "Param removed"
    PARAM_REORDER = "Param reordered"
    PARAM_TYPE = "Param type changed"
    RETURN_TYPE = "Return type changed"

    # Struct changes
    STRUCT_ADD = "Struct added"
    STRUCT_REMOVE = "Struct removed"
    STRUCT_CHANGE = "Struct changed"
    STRUCT_LAYOUT = "Struct layout changed"
    FIELD_ADD = "Field added"
    FIELD_REMOVE = "Field removed"
    FIELD_TYPE = "Field type changed"

    # Enum changes
    ENUM_ADD = "Enum added"
    ENUM_REMOVE = "Enum removed"
    ENUM_CHANGE = "Enum changed"
    VAL_ADD = "Value added"
    VAL_REMOVE = "Value removed"
    VAL_CHANGE = "Value changed"

    # Tracepoint changes
    TRACE_EVENT_CHANGE = "Event changed"
    TRACE_FMT_CHANGE = "Format changed"
    TRACE_FUNC_CHANGE = "Func changed"

    # Config changes
    CONFIG_CHANGE = "Config changed"

    @property
    def consequence(self):
        d = {
            self.OK: Consequence.OK,
            self.ABSENT: Consequence.ERROR,
            self.PARAM_ADD: Consequence.STRAY,
            self.PARAM_REMOVE: Consequence.STRAY,
            self.PARAM_TYPE: Consequence.STRAY,
            self.PARAM_REORDER: Consequence.STRAY,
            self.RETURN_TYPE: Consequence.STRAY,
            self.SELECTIVE_INLINE: Consequence.MISS,
            self.FULL_INLINE: Consequence.ERROR,
            self.TRANSFORMATION: Consequence.ERROR,
            self.DUPLICATE: Consequence.MISS,
            self.FIELD_TYPE: Consequence.STRAY,
        }
        return d.get(self, Consequence.UNKNOWN)

    def __repr__(self):
        return f"'{self.value}'"
