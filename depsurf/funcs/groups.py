import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Iterator, Optional

from depsurf.utils import check_result_path
from depsurf.linux import SymbolTable

from .entry import FuncEntry
from .group import FuncGroup
from .symbol import get_func_symbols, FuncSymbol


class FuncGroups:
    def __init__(self, data: Dict[str, FuncGroup]):
        self.data: Dict[str, FuncGroup] = data

    @property
    def num_groups(self) -> int:
        return len(self.data)

    def get_group(self, name) -> Optional[FuncGroup]:
        return self.data.get(name)

    def iter_groups(self) -> Iterator[FuncGroup]:
        for group in self.data.values():
            yield group

    def iter_funcs(self) -> Iterator[FuncEntry]:
        for group in self.data.values():
            for func in group.funcs:
                yield func

    def iter_symbols(self) -> Iterator[FuncSymbol]:
        for group in self.data.values():
            for symbol in group.symbols:
                yield symbol

    def __str__(self):
        return f"FuncGroups({self.num_groups} groups)"

    @classmethod
    def from_dump(cls, path: Path):
        logging.info(f"Loading funcs from {path}")
        result: Dict[str, FuncGroup] = {}
        with open(path, "r") as f:
            for line in f:
                group = FuncGroup.from_json(line)
                result[group.name] = group
        return cls(data=result)


@check_result_path
def dump_func_groups(funcs_path: Path, symtab_path: Path, result_path: Path):
    functions: Dict[str, List[FuncEntry]] = defaultdict(list)

    with open(funcs_path, "r") as f:
        for line in f:
            func = FuncEntry.from_json(line)
            functions[func.name].append(func)

    func_symbols = get_func_symbols(SymbolTable.from_dump(symtab_path))

    data = {
        name: FuncGroup.from_funcs(funcs, func_symbols.get(name) or [])
        for name, funcs in functions.items()
    }

    with open(result_path, "w") as f:
        for group in data.values():
            print(group.to_json(), file=f)

    logging.info(f"Dumped to {result_path}")
