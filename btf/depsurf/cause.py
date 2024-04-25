from enum import StrEnum


class Consequence(StrEnum):
    COMPILER = "Compiler error"
    RUNTIME = "Runtime error"
    SLIENT = "Silent error"
    CORE = "CO-RE"

    def __repr__(self):
        return f"'{self.value}'"


class BaseCause(StrEnum):
    @property
    def consequence(self):
        raise NotImplementedError

    @property
    def color(self):
        raise NotImplementedError

    def __repr__(self):
        return f"'{self.value}'"


class GenericCause(BaseCause):
    ADD = "Added"
    REMOVE = "Removed"
    FUNC_ADD = "Function added"
    FUNC_REMOVE = "Function removed"
    FUNC_UNAVAIL = "Function unavailable"
    STRUCT_ADD = "Struct added"
    STRUCT_REMOVE = "Struct removed"
    STRUCT_UNAVAIL = "Struct unavailable"
    STATIC_FN = "Static function"
    PARTIAL_INLINE = "Partial inline"
    FULL_INLINE = "Full inline"

    @property
    def consequence(self):
        return {
            self.FUNC_ADD: Consequence.RUNTIME,
            self.FUNC_REMOVE: Consequence.RUNTIME,
            self.FUNC_UNAVAIL: Consequence.RUNTIME,
            self.STRUCT_ADD: Consequence.COMPILER,
            self.STRUCT_REMOVE: Consequence.COMPILER,
            self.STRUCT_UNAVAIL: Consequence.COMPILER,
            self.STATIC_FN: Consequence.RUNTIME,
            self.PARTIAL_INLINE: Consequence.SLIENT,
            self.FULL_INLINE: Consequence.RUNTIME,
        }[self]

    @property
    def color(self):
        return {
            self.ADD: "tab:blue",
            self.REMOVE: "tab:orange",
        }[self]


class FuncCause(BaseCause):
    FUNC_ADD = "Function added"
    FUNC_REMOVE = "Function removed"
    PARAM_ADD = "Param added"
    PARAM_REMOVE = "Param removed"
    PARAM_REORDER = "Param reordered"
    PARAM_TYPE = "Param type changed"
    FUNC_RETURN = "Return type changed"

    @property
    def consequence(self):
        return {
            FuncCause.PARAM_ADD: Consequence.SLIENT,
            FuncCause.PARAM_REMOVE: Consequence.SLIENT,
            FuncCause.PARAM_TYPE: Consequence.SLIENT,
            FuncCause.PARAM_REORDER: Consequence.SLIENT,
            FuncCause.FUNC_RETURN: Consequence.SLIENT,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        cmap = cm.Greens
        return {
            self.PARAM_ADD: cmap(0.3),
            self.PARAM_REMOVE: cmap(0.45),
            self.PARAM_REORDER: cmap(0.6),
            self.PARAM_TYPE: cmap(0.75),
            self.FUNC_RETURN: cmap(0.9),
        }[self]


class StructCause(BaseCause):
    STRUCT_ADD = "Struct added"
    STRUCT_REMOVE = "Struct removed"
    FIELD_ADD = "Field added"
    FIELD_REMOVE = "Field removed"
    FIELD_TYPE = "Field type changed"
    # LAYOUT = "Layout changed"

    @property
    def consequence(self):
        return {
            StructCause.FIELD_ADD: Consequence.COMPILER,
            StructCause.FIELD_REMOVE: Consequence.COMPILER,
            StructCause.FIELD_TYPE: Consequence.SLIENT,
            # StructChange.LAYOUT: Consequence.CORE,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        cmap = cm.Purples
        return {
            self.FIELD_ADD: cmap(0.3),
            self.FIELD_REMOVE: cmap(0.5),
            self.FIELD_TYPE: cmap(0.7),
        }[self]


class EnumCause(BaseCause):
    ENUM_ADD = "Enum added"
    ENUM_REMOVE = "Enum removed"
    VAL_ADD = "Value added"
    VAL_REMOVE = "Value removed"
    VAL_CHANGE = "Value changed"

    @property
    def consequence(self):
        return {
            EnumCause.VAL_ADD: Consequence.COMPILER,
            EnumCause.VAL_REMOVE: Consequence.COMPILER,
            EnumCause.VAL_CHANGE: Consequence.CORE,
        }[self]


def cause_sort_key(cause):
    type_weight = {
        str: 0,
        GenericCause: 1,
        StructCause: 2,
        FuncCause: 3,
        EnumCause: 4,
    }[type(cause)]
    return type_weight, cause
