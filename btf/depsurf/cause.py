from enum import StrEnum


class Consequence(StrEnum):
    COMPILER = "Compiler error"
    RUNTIME = "Runtime error"
    SLIENT = "Silent error"
    CORE = "CO-RE"


class GenericChange(StrEnum):
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


class FuncChange(StrEnum):
    ADD = "Param added"
    REMOVE = "Param removed"
    TYPE = "Param type changed"
    REORDER = "Param reordered"
    RETURN = "Return type changed"

    @property
    def consequence(self):
        return {
            FuncChange.ADD: Consequence.SLIENT,
            FuncChange.REMOVE: Consequence.SLIENT,
            FuncChange.TYPE: Consequence.SLIENT,
            FuncChange.REORDER: Consequence.SLIENT,
            FuncChange.RETURN: Consequence.SLIENT,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        cmap = cm.Greens
        return {
            self.ADD: cmap(0.3),
            self.REMOVE: cmap(0.45),
            self.TYPE: cmap(0.6),
            self.REORDER: cmap(0.75),
            self.RETURN: cmap(0.9),
        }[self]


class StructChange(StrEnum):
    ADD = "Field added"
    REMOVE = "Field removed"
    TYPE = "Field type changed"
    LAYOUT = "Layout changed"

    @property
    def consequence(self):
        return {
            StructChange.ADD: Consequence.COMPILER,
            StructChange.REMOVE: Consequence.COMPILER,
            StructChange.TYPE: Consequence.SLIENT,
            StructChange.LAYOUT: Consequence.CORE,
        }[self]

    @property
    def color(self):
        from matplotlib import cm

        cmap = cm.Purples
        return {
            self.ADD: cmap(0.3),
            self.REMOVE: cmap(0.5),
            self.TYPE: cmap(0.7),
        }[self]


class EnumChange(StrEnum):
    ADD = "Elem added"
    REMOVE = "Elem removed"
    VALUE = "Value changed"

    @property
    def consequence(self):
        return {
            EnumChange.ADD: Consequence.COMPILER,
            EnumChange.REMOVE: Consequence.COMPILER,
            EnumChange.VALUE: Consequence.CORE,
        }[self]
