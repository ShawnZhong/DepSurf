import logging
from pathlib import Path
from typing import Dict

from .entry import FuncEntry
from .group import FuncGroup


class FuncGroups:
    def __init__(self, data=None):
        self.data: Dict[str, FuncGroup] = data or {}

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

    def get_df(self):
        import pandas as pd

        return pd.DataFrame([f.to_dict() for f in self.iter_funcs()])

    def __str__(self):
        return f"FuncGroups({self.num_groups} groups, {self.num_funcs} functions)"

    @classmethod
    def from_dump(cls, path):
        logging.info(f"Loading funcs from {path}")
        result: Dict[str, FuncGroup] = {}
        with open(path, "r") as f:
            for line in f:
                func = FuncEntry.from_json(line)
                group = result.get(func.name)
                if group is None:
                    group = FuncGroup([func])
                    result[func.name] = group
                else:
                    group.add_func(func)

        return cls(result)
