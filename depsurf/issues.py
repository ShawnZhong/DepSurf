from enum import StrEnum
from typing import List


class Consequence(StrEnum):
    # Rank by severity, don't change the order
    MISS = "Missing invocation"
    STRAY = "Stray read"
    ERROR = "Error"
    OK = "OK"
    UNKNOWN = "Unknown"

    @property
    def color(self):
        return {
            self.MISS: "tab:red",
            self.STRAY: "tab:orange",
            self.ERROR: "tab:blue",
            self.OK: "tab:green",
            self.UNKNOWN: "white",
        }[self]


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
    STATIC = "Static"
    PARTIAL_INLINE = "Par. Inline"
    FULL_INLINE = "Full Inline"
    RENAME = "Renamed"
    DUPLICATE = "Duplicate"

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
            self.PARTIAL_INLINE: Consequence.MISS,
            self.FULL_INLINE: Consequence.ERROR,
            self.RENAME: Consequence.ERROR,
            self.STATIC: Consequence.OK,
            self.DUPLICATE: Consequence.MISS,
            self.FIELD_TYPE: Consequence.STRAY,
        }
        return d.get(self, Consequence.UNKNOWN)

    @property
    def color(self):
        return self.consequence.color

        from matplotlib import cm

        fn_cmap = cm.Greens
        struct_cmap = cm.Purples
        return {
            # Generic status
            self.OK: "tab:green",
            self.ABSENT: "tab:red",
            # Generic changes
            self.ADD: "white",  # "tab:blue",
            self.REMOVE: "white",  # "tab:red",
            self.CHANGE: "tab:orange",
            self.NO_CHANGE: "white",  # "whitesmoke",
            self.BOTH_ABSENT: "white",
            # Function status
            self.STATIC: "gray",
            self.DUPLICATE: "black",
            self.RENAME: "blue",
            self.PARTIAL_INLINE: "tab:blue",
            self.FULL_INLINE: "darkblue",
            # Function changes
            self.PARAM_ADD: fn_cmap(0.3),
            self.PARAM_REMOVE: fn_cmap(0.45),
            self.PARAM_REORDER: fn_cmap(0.6),
            self.PARAM_TYPE: fn_cmap(0.75),
            self.RETURN_TYPE: fn_cmap(0.9),
            # Struct changes
            self.FIELD_ADD: struct_cmap(0.3),
            self.FIELD_REMOVE: struct_cmap(0.5),
            self.FIELD_TYPE: struct_cmap(0.7),
        }[self]

    def get_symbol(self, emoji=False):
        return {
            # Generic
            self.OK: "" if not emoji else "✅",
            self.ABSENT: "" if not emoji else "❌",  # "✗"
            self.ADD: "" if not emoji else "🔺",  # "+"
            self.REMOVE: "" if not emoji else "🔻",  # "-"
            self.NO_CHANGE: "",  # ".",
            self.CHANGE: r"$\Delta$",
            self.BOTH_ABSENT: "",
            # Fuction status
            self.STATIC: "S" if not emoji else "🟣S",
            self.PARTIAL_INLINE: "P" if not emoji else "🟡P",
            self.FULL_INLINE: "F" if not emoji else "🟠F",
            self.RENAME: "R" if not emoji else "🔵R",
            self.DUPLICATE: "D" if not emoji else "🟣D",
            # Function changes
            self.PARAM_ADD: "P+",
            self.PARAM_REMOVE: "P-",
            self.PARAM_REORDER: "PR",
            self.PARAM_TYPE: "PT",
            self.RETURN_TYPE: "RT",
            # Struct changes
            self.FIELD_ADD: "F+",
            self.FIELD_REMOVE: "F-",
            self.FIELD_TYPE: "FT",
        }[self]

    def __repr__(self):
        return f"'{self.value}'"


class IssueList:
    def __init__(self, *issues: IssueEnum):
        self.issues: List[IssueEnum] = list(e for e in issues if e != IssueEnum.STATIC)

    def append(self, issue: IssueEnum):
        self.issues.append(issue)

    @property
    def color(self):
        issues = set(e for e in self.issues if e != IssueEnum.STATIC)
        if len(issues) == 0:
            return "tab:green"
        if IssueEnum.ABSENT in self.issues:
            return "lightgray"
        return "tab:red"

    @property
    def text(self):
        issues = set(e for e in self.issues if e != IssueEnum.STATIC)
        return "".join([e.get_symbol() for e in issues])

    def __iter__(self):
        return iter(self.issues)

    def __len__(self):
        return len(self.issues)

    def __iadd__(self, other):
        self.issues += other.issues
        return self

    def __repr__(self):
        return repr([e for e in self.issues])

    def __contains__(self, item):
        return item in self.issues
