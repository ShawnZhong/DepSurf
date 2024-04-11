import logging
from functools import cached_property
from pathlib import Path

from .kind import Kind


class BTF:
    def __init__(self, path):
        import pickle

        self.path = Path(path)
        assert self.path.exists()
        assert self.path.suffix == ".pkl"
        with open(self.path, "rb") as f:
            logging.info(f"Loading BTF from {self.path}")
            self.data = pickle.load(f)

    def __repr__(self):
        result = f"File: {self.path}\n"
        result += "Sample:\n"
        for kind, d in self.data.items():
            result += f"\t{kind:10} ({len(d):5}): {list(d.values())[0]}\n"
        return result

    def get(self, kind, name):
        return self.data[kind].get(name)

    def get_all_kind(self, kind: Kind):
        return self.data[kind]

    def get_func(self, name: str):
        return self.data[Kind.FUNC].get(name)

    def get_struct(self, name: str):
        return self.data[Kind.STRUCT].get(name)

    def get_enum(self, name: str):
        return self.data[Kind.ENUM].get(name)

    def get_union(self, name: str):
        return self.data[Kind.UNION].get(name)

    @cached_property
    def enum_values(self):
        return {e["name"]: e["val"] for e in self.get(Kind.ENUM, "(anon)")["values"]}
