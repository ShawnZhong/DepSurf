from enum import Enum


class Consequence(str, Enum):
    COMPILER = "Compiler error"
    RUNTIME = "Runtime error"
    SLIENT = "Silent error"
    CORE = "CO-RE"


class GenericChange(str, Enum):
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


class FuncChange(str, Enum):
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


class StructChange(str, Enum):
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


class EnumChange(str, Enum):
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
