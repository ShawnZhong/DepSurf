from enum import StrEnum


class Consequence(StrEnum):
    COMPILER = "Compiler error"
    RUNTIME = "Runtime error"
    SLIENT = "Silent error"
    CORE = "CO-RE"

    def __repr__(self):
        return f"'{self.value}'"


class BaseCause:
    def __init_subclass__(cls, enum):
        cls.enum = enum

    def format(self):
        raise NotImplementedError

    def __str__(self):
        return f"{self.enum:24}{self.format()}"


class BaseCauseEnum(StrEnum):
    def __init_subclass__(cls, sort_idx):
        cls.sort_idx = sort_idx

    @property
    def consequence(self):
        raise NotImplementedError

    @property
    def color(self):
        raise NotImplementedError

    def __repr__(self):
        return f"'{self.value}'"


class GenericCauses(BaseCauseEnum, sort_idx=1):
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
