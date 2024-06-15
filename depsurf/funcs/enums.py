from enum import StrEnum
from depsurf.utils import OrderedEnum


class CollisionType(StrEnum):
    UNIQUE_GLOBAL = "Unique Global"
    UNIQUE_STATIC = "Unique Static"
    INCLUDE_DUP = "Static Duplication"
    STATIC_STATIC = "Static-Static Collision"
    STATIC_GLOBAL = "Static-Global Collision"


class InlineType(OrderedEnum, StrEnum):
    NOT = "Not inlined"
    FULL = "Fully inlined"
    PARTIAL = "Partially inlined"


class RenameType(StrEnum):
    ISRA = "isra"
    CONSTPROP = "constprop"
    PART = "part"
    COLD = "cold"
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
