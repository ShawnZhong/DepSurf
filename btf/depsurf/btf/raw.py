from .kind import Kind


def load_btf_json(path):
    import json

    with open(path) as f:
        return json.load(f)["types"]


def get_btf_type_str(obj):
    assert "kind" in obj, obj
    kind = obj["kind"]

    if kind in (Kind.STRUCT, Kind.UNION, Kind.ENUM, Kind.VOLATILE, Kind.CONST):
        return f"{kind.lower()} {obj['name']}"
    elif kind in (Kind.TYPEDEF, Kind.INT, Kind.VOID):
        return obj["name"]
    elif kind == Kind.PTR:
        if obj["type"]["kind"] == Kind.FUNC_PROTO:
            return get_btf_type_str(obj["type"])
        else:
            return f"{get_btf_type_str(obj['type'])} *"
    elif kind == Kind.ARRAY:
        return f"{get_btf_type_str(obj['type'])}[{obj['nr_elems']}]"
    elif kind == Kind.FUNC_PROTO:
        return f"{get_btf_type_str(obj['ret_type'])} (*)({', '.join(get_btf_type_str(a['type']) for a in obj['params'])})"
    elif kind == Kind.FWD:
        return f"{obj['fwd_kind']} {obj['name']}"
    else:
        raise ValueError(f"Unknown kind: {obj}")


class RawBTF:
    def __init__(self, raw_types):
        self.raw_types = raw_types

    @classmethod
    def load(cls, path):
        return cls(load_btf_json(path))

    def get_raw(self, type_id):
        elem = self.raw_types[type_id - 1]
        assert elem["id"] == type_id
        return elem

    def __len__(self):
        return len(self.raw_types)

    def __repr__(self):
        return f"RawBTF({len(self.raw_types)} types)"
