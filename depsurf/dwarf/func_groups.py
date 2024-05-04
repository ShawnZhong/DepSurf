from typing import List, Tuple
import logging

from pathlib import Path
from .func_entry import FuncEntry


class FuncGroups:
    def __init__(self, data=None):
        self.data: List[Tuple[str, List[FuncEntry]]] = data if data is not None else []

    @property
    def num_funcs(self):
        return sum(len(group) for _, group in self.data)

    def add_group(self, name, group):
        self.data.append((name, group))

    def print_groups(self, file=None):
        print(f"{len(self.data)} groups, {self.num_funcs} functions", file=file)
        for name, group in sorted(self.data, key=lambda x: len(x[1]), reverse=True):
            print(f"{name} ({len(group)})", file=file)
            for func in group:
                if func.external:
                    print(f"  {func.file} (external)", file=file)
                else:
                    print(f"  {func.file}", file=file)

    def save_result(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            self.print_groups(f)
        logging.info(f"Saved {len(self.data)} groups to {path}")

    @classmethod
    def from_jsonl(cls, path):
        result = {}
        with open(path, "r") as f:
            for line in f:
                func = FuncEntry.from_json(line)
                result.setdefault(func.name, []).append(func)

        return cls(result.items())
