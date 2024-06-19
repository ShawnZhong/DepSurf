from typing import Dict, List, Optional


class FuncSymbolGroup:
    def __init__(self, name: str, symbols: Optional[List[Dict]] = None):
        self.name = name
        self.symbols = symbols if symbols is not None else []

    def add(self, symbol: Dict):
        assert symbol["type"] == "STT_FUNC"
        self.symbols.append(symbol)

    @property
    def has_suffix(self):
        return any("." in sym["name"] for sym in self.symbols)

    def __repr__(self):
        return f"FuncSymbolGroup({self.name}, {len(self.symbols)} symbols)"

    def __iter__(self):
        return iter(self.symbols)

    def print(self, file=None, nindent=0):
        indent = "\t" * nindent
        for sym in self.symbols:
            print(
                f"{indent}"
                f"FuncSymbol("
                f"addr={hex(sym['value'])}, "
                f"name={sym['name']}, "
                f"section={sym['section']}, "
                f"bind={sym['bind']}, "
                f"size={sym['size']}"
                f")",
                file=file,
            )
