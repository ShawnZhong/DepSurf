from enum import StrEnum

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
