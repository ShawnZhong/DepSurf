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
    else:
        raise ValueError(f"Unknown kind: {obj}")
