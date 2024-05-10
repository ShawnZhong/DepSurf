from enum import StrEnum


class CollisionType(StrEnum):
    UNIQUE_GLOBAL = "Unique Global"
    UNIQUE_STATIC = "Unique Static"
    INCLUDE_DUP = "Duplication with #include"
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
