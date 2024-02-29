from .btf_kind import Kind


class BTFNormalizer:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    RECURSE_KINDS = {
        Kind.CONST,
        Kind.VOLATILE,
        Kind.RESTRICT,
        Kind.PTR,
        Kind.FUNC,
        Kind.FUNC_PROTO,
        Kind.ARRAY,
    }

    def normalize_int(self, elem):
        assert elem["bits_offset"] == 0
        del elem["bits_offset"]
        del elem["encoding"]
        del elem["nr_bits"]
        del elem["size"]

    @staticmethod
    def uint2sint(u, nbytes):
        nbits = nbytes * 8
        u &= (1 << nbits) - 1
        if u >= (1 << (nbits - 1)):
            return u - (1 << nbits)
        return u

    def normalize_enum(self, elem, recurse):
        assert elem["vlen"] == len(elem["values"])
        del elem["vlen"]

        if recurse:
            if elem["encoding"] == "UNSIGNED":
                elem["values"] = [
                    {**v, "val": self.uint2sint(v["val"], elem["size"])}
                    for v in elem["values"]
                ]
        else:
            del elem["values"]
        del elem["encoding"]

    def normalize_type_id(self, elem, recurse):
        for type_key in ["type", "ret_type"]:
            type_id = f"{type_key}_id"

            if type_id not in elem:
                continue

            if recurse:
                elem[type_key] = self.normalize_impl(elem[type_id])
            del elem[type_id]

    def get_new_list(self, old_list):
        anon_count = 0

        def new_item(item):
            name = item["name"]
            if name == "(anon)":
                nonlocal anon_count

                if anon_count > 0:
                    name = f"(anon-{anon_count})"
                anon_count += 1

            return {
                "name": name,
                **{k: v for k, v in item.items() if k not in ["name", "type_id"]},
                "type": self.normalize_impl(item["type_id"]),
            }

        return [new_item(item) for item in old_list]

    def normalize_list(self, elem, recurse):
        for list_key in ["params", "members"]:
            if list_key not in elem:
                continue

            assert len(elem[list_key]) == elem["vlen"]
            del elem["vlen"]

            if recurse:
                elem[list_key] = self.get_new_list(elem[list_key])
            else:
                del elem[list_key]
                if list_key == "members":
                    del elem["size"]

    def normalize_impl(self, type_id, recurse=False):
        if type_id == 0:
            return {"name": "void", "kind": "VOID"}

        elem = self.raw_data[type_id - 1]
        assert elem["id"] == type_id

        kind = elem["kind"]

        # Recurse into types for certain kinds
        recurse = recurse or kind in self.RECURSE_KINDS

        elem = elem.copy()

        del elem["id"]

        if kind == Kind.INT:
            self.normalize_int(elem)
        elif kind == Kind.ARRAY:
            del elem["index_type_id"]
        elif kind == Kind.ENUM:
            self.normalize_enum(elem, recurse)
        elif kind == Kind.FUNC:
            assert elem["linkage"] == "static"
            del elem["linkage"]
        elif kind in (Kind.PTR, Kind.FUNC_PROTO):
            assert elem["name"] == "(anon)"
            del elem["name"]

        self.normalize_type_id(elem, recurse)
        self.normalize_list(elem, recurse)

        return elem

    def normalize(self, type_id):
        return self.normalize_impl(type_id, recurse=True)


def normalize_btf(file, overwrite=False):
    import json
    from collections import defaultdict
    import pickle

    jsonl_path = file.with_suffix(".jsonl")
    pkl_path = file.with_suffix(".pkl")

    if jsonl_path.exists() and pkl_path.exists() and not overwrite:
        print(f"{jsonl_path} already exists")
        print(f"{pkl_path} already exists")
        with open(pkl_path, "rb") as f:
            return pickle.load(f)

    json_path = file.with_suffix(".json")
    assert json_path.exists()

    with open(json_path) as f:
        data = json.load(f)["types"]
        normalizer = BTFNormalizer(data)

        result = []
        result_by_kind = defaultdict(dict)
        for i in range(1, len(data) + 1):
            t = normalizer.normalize(i)
            result.append(t)
            if "name" not in t:
                continue
            name = t["name"]
            if name != "(anon)":
                result_by_kind[t["kind"]][name] = t

        print(f"Writing {jsonl_path}")
        with open(jsonl_path, "w") as f:
            for elem in result:
                f.write(json.dumps(elem) + "\n")

        print(f"Writing {pkl_path}")
        with open(pkl_path, "wb") as f:
            pickle.dump(dict(result_by_kind), f)

        return result_by_kind
