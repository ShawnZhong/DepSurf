from enum import StrEnum


class Consequence(StrEnum):
    COMPILER = "Compiler error"
    RUNTIME = "Runtime error"
    SLIENT = "Silent error"
    CORE = "CO-RE"

    def __repr__(self):
        return f"'{self.value}'"


class IssueEnum(StrEnum):
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
    TRACE_FUNC_CHANGE = "Func changed"

    # Config changes
    CONFIG_CHANGE = "Config changed"

    @property
    def consequence(self):
        return {
            # Function
            self.PARAM_ADD: Consequence.SLIENT,
            self.PARAM_REMOVE: Consequence.SLIENT,
            self.PARAM_TYPE: Consequence.SLIENT,
            self.PARAM_REORDER: Consequence.SLIENT,
            self.RETURN_TYPE: Consequence.SLIENT,
            # Struct
            self.FIELD_ADD: Consequence.COMPILER,
            self.FIELD_REMOVE: Consequence.COMPILER,
            self.FIELD_TYPE: Consequence.SLIENT,
            # Enum
            self.VAL_ADD: Consequence.COMPILER,
            self.VAL_REMOVE: Consequence.COMPILER,
            self.VAL_CHANGE: Consequence.CORE,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        fn_cmap = cm.Greens
        struct_cmap = cm.Purples
        return {
            # Generic status
            self.OK: "tab:green",
            self.ABSENT: "tab:red",
            # Generic changes
            self.ADD: "tab:blue",
            self.REMOVE: "tab:red",
            self.CHANGE: "tab:orange",
            self.NO_CHANGE: "whitesmoke",
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
            self.ABSENT: "✗" if not emoji else "❌",
            self.ADD: "+" if not emoji else "🔺",
            self.REMOVE: "-" if not emoji else "🔻",
            self.NO_CHANGE: ".",
            self.CHANGE: "42",
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
