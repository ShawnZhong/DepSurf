from enum import StrEnum


class CollisionType(StrEnum):
    UNIQUE = "Unique"
    HEADER = "Include Duplication"
    STATIC = "Static-Static Collision"
    MIXED = "Static-Global Collision"

    @property
    def color(self):
        return {
            CollisionType.UNIQUE: "tab:blue",
            CollisionType.HEADER: "tab:orange",
            CollisionType.STATIC: "darkslateblue",
            CollisionType.MIXED: "tab:green",
        }[self]


class InlineType(StrEnum):
    FULL = "Fully inlined"
    NOT = "Not inlined"
    PARTIAL = "Partially inlined"

    @property
    def color(self):
        return {
            InlineType.FULL: "slateblue",
            InlineType.NOT: "tab:green",
            InlineType.PARTIAL: "tab:red",
        }[self]
