import json
import logging
from pathlib import Path
from typing import Dict

from .kind import Kind


def get_type_str(obj):
    assert "kind" in obj, obj
    kind = obj["kind"]

    if kind in (Kind.STRUCT, Kind.UNION, Kind.ENUM, Kind.VOLATILE, Kind.CONST):
        return f"{kind.lower()} {obj['name']}"
    elif kind in (Kind.TYPEDEF, Kind.INT, Kind.VOID):
        return obj["name"]
    elif kind == Kind.PTR:
        if obj["type"]["kind"] == Kind.FUNC_PROTO:
            return get_type_str(obj["type"])
        else:
            return f"{get_type_str(obj['type'])} *"
    elif kind == Kind.ARRAY:
        return f"{get_type_str(obj['type'])}[{obj['nr_elems']}]"
    elif kind == Kind.FUNC_PROTO:
        return f"{get_type_str(obj['ret_type'])} (*)({', '.join(get_type_str(a['type']) for a in obj['params'])})"
    elif kind == Kind.FWD:
        return f"{obj['fwd_kind']} {obj['name']}"
    else:
        raise ValueError(f"Unknown kind: {obj}")


class Types:
    def __init__(self, data: dict):
        assert isinstance(data, dict)
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

        data = BTFNormalizer(path).get_data()
        return cls(data[kind])
