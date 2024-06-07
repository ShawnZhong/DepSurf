from enum import StrEnum


class CollisionType(StrEnum):
    UNIQUE_GLOBAL = "Unique Global"
    UNIQUE_STATIC = "Unique Static"
    INCLUDE_DUP = "Static Dup. with #include"
    STATIC_STATIC = "Static-Static Collision"
    STATIC_GLOBAL = "Static-Global Collision"

    @property
    def color(self):
        return {
            # CollisionType.UNIQUE_GLOBAL: "tab:blue",
            # CollisionType.UNIQUE_STATIC: "tab:red",
            CollisionType.INCLUDE_DUP: "tab:blue",
            CollisionType.STATIC_STATIC: "tab:red",
            CollisionType.STATIC_GLOBAL: "tab:green",
        }[self]


class InlineType(StrEnum):
    FULL = "Fully inlined"
    NOT = "Not inlined"
    PARTIAL = "Partially inlined"

    @property
    def color(self):
        return {
            InlineType.FULL: "tab:blue",
            InlineType.NOT: "tab:green",
            InlineType.PARTIAL: "tab:red",
        }[self]


class RenameType(StrEnum):
    ISRA = "ISRA"
    CONSTPROP = "Const Propagation"
    PART = "Part"
    COLD = "Cold"
    MULTIPLE = "≥2"

    @classmethod
    def from_suffix(cls, suffix):
        if "." in suffix:
            return cls.MULTIPLE
        return {
            "isra": cls.ISRA,
            "constprop": cls.CONSTPROP,
            "part": cls.PART,
            "cold": cls.COLD,
        }[suffix]

    @property
    def color(self):
        return {
            RenameType.ISRA: "C0",
            RenameType.PART: "C1",
            RenameType.COLD: "C2",
            RenameType.CONSTPROP: "C3",
            RenameType.MULTIPLE: "C4",
        }[self]
