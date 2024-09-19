from dataclasses import dataclass

from collections import defaultdict
from typing import Dict, List
import logging

from depsurf.linux import SymbolTable

@dataclass
class FuncSymbol:
    addr: int
    name: str
    section: str
    bind: str
    size: int


def get_func_symbols(symtab: SymbolTable) -> Dict[str, List[FuncSymbol]]:
    result: Dict[str, List[FuncSymbol]] = defaultdict(list)
    for sym in symtab.data:
        if sym["type"] != "STT_FUNC":
            continue
        name: str = sym["name"]
        # Ref: https://github.com/torvalds/linux/commit/9f2899fe36a623885d8576604cb582328ad32b3c
        if name.startswith("__pfx"):
            continue
        group_name = name.split(".")[0]
        if sym["visibility"] != "STV_DEFAULT":
            logging.debug(f"Symbol {name} is not default visibility: {sym}")
        func_sym = FuncSymbol(
            addr=sym["value"],
            name=sym["name"],
            section=sym["section"],
            bind=sym["bind"],
            size=sym["size"],
        )
        result[group_name].append(func_sym)

    return result