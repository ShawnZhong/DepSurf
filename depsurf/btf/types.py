import json
import logging
from pathlib import Path
from typing import Dict

from .kind import Kind


class Types:
    def __init__(self, data: Dict):
        assert isinstance(data, Dict)
        self.data: Dict[str, Dict] = data

    @classmethod
    def from_dump(cls, path: Path):
        assert path.exists()
        assert path.suffix == ".jsonl"
        with open(path, "r") as f:
            logging.info(f"Loading types from {path}")

            data = {}
            for line in f:
                info = json.loads(line)
                data[info["name"]] = info

            return cls(data)

    @classmethod
    def from_btf_json(cls, path: Path, kind: Kind):
        assert path.exists()
        assert path.suffix == ".json"
        from .dump import BTFNormalizer

        data = BTFNormalizer(path).data
        return cls(data[kind])

    def __getitem__(self, name: str):
        return self.data[name]

    def get(self, name: str):
        return self.data.get(name)

    def items(self):
        return self.data.items()

    def __iter__(self):
        return iter(self.data)
