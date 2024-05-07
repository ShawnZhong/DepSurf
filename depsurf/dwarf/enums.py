from enum import StrEnum
from dataclasses import dataclass


class CollisionType(StrEnum):
    UNIQUE_GLOBAL = "Unique Global"
    UNIQUE_STATIC = "Unique Static"
    INCLUDE = "Duplication with #include"
    STATIC = "Static-Static Collision"
    MIXED = "Static-Global Collision"

    @property
    def color(self):
        return {
            # CollisionType.UNIQUE_GLOBAL: "tab:blue",
            # CollisionType.UNIQUE_STATIC: "tab:red",
            CollisionType.INCLUDE: "tab:blue",
            CollisionType.STATIC: "tab:red",
            CollisionType.MIXED: "tab:green",
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
