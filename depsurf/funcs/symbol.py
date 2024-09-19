from dataclasses import dataclass

from collections import defaultdict
from typing import Dict, List
import logging

from depsurf.linux import SymbolTable

from enum import StrEnum

class RenameType(StrEnum):
    ISRA = "isra"
    CONSTPROP = "constprop"
    PART = "part"
    COLD = "cold"
    LOCALALIAS = "localalias"
    MULTIPLE = "≥2"


@dataclass
class FuncSymbol:
    addr: int
    name: str
    section: str
    bind: str
    size: int

    @property
    def stem(self) -> str:
        return self.name.split(".")[0]
    
    @property
    def has_suffix(self) -> bool:
        return "." in self.name
    
    @property
    def suffix(self) -> List[str]:
        return [s for s in self.name.split(".")[1:] if not s.isdigit()]
    
    @property
    def rename_type(self) -> RenameType:
        assert self.has_suffix, "Symbol has no suffix"
        suffix = self.suffix
        if len(suffix) > 1:
            return RenameType.MULTIPLE
        return RenameType(suffix[0])


def get_func_symbols(symtab: SymbolTable) -> Dict[str, List[FuncSymbol]]:
    result: Dict[str, List[FuncSymbol]] = defaultdict(list)
    for sym in symtab.data:
        if sym["type"] != "STT_FUNC":
            continue
        name: str = sym["name"]
        # Ref: https://github.com/torvalds/linux/commit/9f2899fe36a623885d8576604cb582328ad32b3c
        if name.startswith("__pfx"):
            continue
        if sym["visibility"] != "STV_DEFAULT":
            logging.debug(f"Symbol {name} is not default visibility: {sym}")
        func_sym = FuncSymbol(
            addr=sym["value"],
            name=sym["name"],
            section=sym["section"],
            bind=sym["bind"],
            size=sym["size"],
        )
        result[func_sym.stem].append(func_sym)

    return result