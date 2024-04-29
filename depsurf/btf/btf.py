import logging
import pickle
from functools import cached_property
from pathlib import Path

from .kind import Kind


class BTF:
    def __init__(self, data: dict):
        assert isinstance(data, dict)
        self.data = data

    @classmethod
    def from_dump(cls, path: Path):
        assert path.exists()
        assert path.suffix == ".pkl"
        with open(path, "rb") as f:
            logging.info(f"Loading BTF from {path}")
            return cls(pickle.load(f))

    @classmethod
    def from_raw_json(cls, path: Path):
        assert path.exists()
        assert path.suffix == ".json"
        from .normalize import BTFNormalizer

        data = BTFNormalizer.from_json_path(path).get_results_by_kind()
        return cls(data)

    def __str__(self):
        return "\n".join(
            f"{kind:10} ({len(d):5}): {list(d.values())[0]}"
            for kind, d in self.data.items()
            if d
        )

    def get(self, kind, name):
        return self.data[kind].get(name)

    @property
    def funcs(self) -> dict:
        return self.data[Kind.FUNC]

    @property
    def structs(self) -> dict:
        return self.data[Kind.STRUCT]

    @property
    def enums(self) -> dict:
        return self.data[Kind.ENUM]

    @property
    def unions(self) -> dict:
        return self.data[Kind.UNION]

    def get_func(self, name: str):
        return self.funcs.get(name)

    def get_struct(self, name: str):
        return self.structs.get(name)

    def get_enum(self, name: str):
        return self.enums.get(name)

    def get_union(self, name: str):
        return self.unions.get(name)

    @cached_property
    def enum_values(self):
        return {e["name"]: e["val"] for e in self.get(Kind.ENUM, "(anon)")["values"]}
