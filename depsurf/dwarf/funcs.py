import logging
from pathlib import Path
from typing import List

from .func_entry import FuncEntry


class Funcs:
    def __init__(self, data=None):
        self.data: List[FuncEntry] = data if data is not None else []

    @classmethod
    def from_jsonl(cls, path):
        with open(path) as f:
            data = [FuncEntry.from_json(line) for line in f]
        return cls(data)

    def get_df(self):
        import pandas as pd

        return pd.DataFrame([f.to_dict() for f in self.data])

    def add(self, data):
        self.data.append(data)

    def __repr__(self):
        return f"Functions({len(self.data)})"

    @property
    def num_funcs(self):
        return len(self.data)

    def save_result(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            print(f"{len(self.data)} functions", file=f)
            for d in self.data:
                print(d, file=f)
        logging.info(f"Saved {len(self.data)} functions to {path}")
