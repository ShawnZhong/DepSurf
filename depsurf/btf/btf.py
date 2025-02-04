import json
import logging
from functools import cached_property
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
        self.data = data

    @classmethod
    def from_dump(cls, path: Path):
        assert path.exists()
        assert path.suffix == ".json"
        with open(path, "r") as f:
            logging.info(f"Loading types from {path}")
            return cls(json.load(f))

    @classmethod
    def from_btf_json(cls, path: Path):
        assert path.exists()
        assert path.suffix == ".json"
        from .normalize import BTFNormalizer

        data = BTFNormalizer(path).get_results()
        return cls(data)

    def __str__(self):
        return "\n".join(
            f"{kind:10} ({len(d):5}): {list(d.values())[0]}"
            for kind, d in self.data.items()
            if d
        )

    @property
    def funcs(self) -> Dict[str, Dict]:
        return self.data[Kind.FUNC]

    @property
    def structs(self) -> Dict[str, Dict]:
        return self.data[Kind.STRUCT]

    @property
    def enums(self) -> Dict[str, Dict]:
        return self.data[Kind.ENUM]

    @property
    def unions(self) -> Dict[str, Dict]:
        return self.data[Kind.UNION]

    @cached_property
    def enum_values(self):
        return {e["name"]: e["val"] for e in self.enums["(anon)"]["values"]}
