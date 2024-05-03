import dataclasses
import json
import logging
import pickle
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Dict, Tuple


@dataclass
class FuncEntry:
    name: str
    external: bool
    inline: int = -1  # 2, 3: declared inline; 1, 3: actually inline
    decl_loc: str = None
    file: str = None
    caller_inline: list = dataclasses.field(default_factory=list)
    caller_func: list = dataclasses.field(default_factory=list)


class FunctionGroups:
    def __init__(self, data={}):
        # name -> (location -> FuncEntry)
        self.data: Dict[str, Dict[Tuple[str, str], FuncEntry]] = data

    def get_or_create_group(self, name):
        group = self.data.get(name)
        if group is None:
            group = {}
            self.data[name] = group
        return group

    def __setitem__(self, name, group):
        self.data[name] = group

    @cached_property
    def df(self):
        import pandas as pd

        df = pd.DataFrame(
            [
                dataclasses.asdict(info)
                for loc_dict in self.data.values()
                for info in loc_dict.values()
            ]
        )
        return df

    @cached_property
    def num_groups(self):
        return len(self.data)

    @cached_property
    def num_funcs(self):
        return sum(len(loc_dict) for loc_dict in self.data.values())

    def filter(self, fn):
        return FunctionGroups(
            {
                name: loc_dict
                for name, loc_dict in self.data.items()
                if fn(name, loc_dict)
            }
        )

    def __repr__(self):
        return (
            f"FunctionGroups(num_groups={self.num_groups}, num_funcs={self.num_funcs})"
        )

    def print(self, file=None):
        print(f"{self.num_groups} groups, {self.num_funcs} functions", file=file)
        for name, loc_dict in sorted(
            self.data.items(), key=lambda x: len(x[1]), reverse=True
        ):
            print(f"{name} ({len(loc_dict)})", file=file)
            for decl_loc, file in loc_dict.keys():
                print(f"  {file}", file=file)

    def dump_txt(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            self.print(file=f)
        logging.info(f"Dumped to {path}")

    def dump_pkl(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.data, f)
        logging.info(f"Dumped to {path}")

    def dump_jsonl(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for name, group in self.data.items():
                for loc, func in group.items():
                    print(json.dumps(dataclasses.asdict(func)), file=f)

        logging.info(f"Dumped to {path}")

    @classmethod
    def from_pkl(cls, path):
        with open(path, "rb") as f:
            data = pickle.load(f)
        return cls(data)

    @classmethod
    def from_jsonl(cls, path):
        data = {}
        with open(path, "r") as f:
            for line in f:
                func = FuncEntry(**json.loads(line))
                group = data.get(func.name)
                if group is None:
                    group = {}
                    data[func.name] = group
                group[(func.decl_loc, func.file)] = func
        return cls(data)
