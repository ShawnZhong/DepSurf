import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from depsurf.utils import check_result_path
from depsurf.linux import SymbolTable

from .entry import FuncEntry
from .group import FuncGroup
from .symbol import get_func_symbols


class FuncGroups:
    def __init__(self, data: Dict[str, FuncGroup]):
        self.data: Dict[str, FuncGroup] = data

    @property
    def num_funcs(self):
        return sum(group.num_funcs for group in self.data.values())

    @property
    def num_groups(self):
        return len(self.data)

    def add_group(self, name, group):
        self.data[name] = group

    def get_group(self, name):
        return self.data.get(name)

    def iter_groups(self):
        return self.data.items()

    def iter_funcs(self):
        for group in self.data.values():
            for func in group.funcs:
                yield func

    def print_groups(self, file=None):
        for group in sorted(
            self.data.values(), key=lambda x: x.num_funcs, reverse=True
        ):
            group.print_long(file=file)

    def print_funcs(self, file=None):
        for func in self.iter_funcs():
            func.print_long(file=file)

    def save_groups(self, path: Path):
        self.save_impl(path, self.print_groups)

    def save_funcs(self, path: Path):
        self.save_impl(path, self.print_funcs)

    def save_impl(self, path: Path, print_func):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            print(f"{self}", file=f)
            print_func(f)
        logging.info(f"Saved {self} to {path}")

    def __str__(self):
        return f"FuncGroups({self.num_groups} groups, {self.num_funcs} functions)"

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
def dump_funcs_groups(funcs_path: Path, symtab_path: Path, result_path: Path):
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
