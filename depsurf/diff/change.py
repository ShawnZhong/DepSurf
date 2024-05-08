from enum import StrEnum


class Consequence(StrEnum):
    COMPILER = "Compiler error"
    RUNTIME = "Runtime error"
    SLIENT = "Silent error"
    CORE = "CO-RE"

    def __repr__(self):
        return f"'{self.value}'"


class ChangeEnum(StrEnum):
    # Generic
    ADD = "Added"
    REMOVE = "Removed"
    CHANGE = "Changed"

    # Function
    FUNC_ADD = "Function added"
    FUNC_REMOVE = "Function removed"
    PARAM_ADD = "Param added"
    PARAM_REMOVE = "Param removed"
    PARAM_REORDER = "Param reordered"
    PARAM_TYPE = "Param type changed"
    FUNC_RETURN = "Return type changed"

    # Struct
    STRUCT_ADD = "Struct added"
    STRUCT_REMOVE = "Struct removed"
    FIELD_ADD = "Field added"
    FIELD_REMOVE = "Field removed"
    FIELD_TYPE = "Field type changed"

    # Enum
    ENUM_ADD = "Enum added"
    ENUM_REMOVE = "Enum removed"
    VAL_ADD = "Value added"
    VAL_REMOVE = "Value removed"
    VAL_CHANGE = "Value changed"

    @property
    def consequence(self):
        return {
            # Function
            self.PARAM_ADD: Consequence.SLIENT,
            self.PARAM_REMOVE: Consequence.SLIENT,
            self.PARAM_TYPE: Consequence.SLIENT,
            self.PARAM_REORDER: Consequence.SLIENT,
            self.FUNC_RETURN: Consequence.SLIENT,
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
            self.ADD: "tab:blue",
            self.REMOVE: "tab:orange",
            # Function
            self.PARAM_ADD: fn_cmap(0.3),
            self.PARAM_REMOVE: fn_cmap(0.45),
            self.PARAM_REORDER: fn_cmap(0.6),
            self.PARAM_TYPE: fn_cmap(0.75),
            self.FUNC_RETURN: fn_cmap(0.9),
            # Struct
            self.FIELD_ADD: struct_cmap(0.3),
            self.FIELD_REMOVE: struct_cmap(0.5),
            self.FIELD_TYPE: struct_cmap(0.7),
        }[self]

    @property
    def short(self):
        return {
            # Function
            self.PARAM_ADD: "P+",
            self.PARAM_REMOVE: "P-",
            self.PARAM_REORDER: "PR",
            self.PARAM_TYPE: "PT",
            self.FUNC_RETURN: "RT",
            # Struct
            self.FIELD_ADD: "F+",
            self.FIELD_REMOVE: "F-",
            self.FIELD_TYPE: "FT",
        }[self]

    def __repr__(self):
        return f"'{self.value}'"


class BaseChange:
    def __init_subclass__(cls, enum: ChangeEnum):
        cls.enum = enum

    def format(self):
        raise NotImplementedError

    def __str__(self):
        return f"{self.enum:24}{self.format()}"
