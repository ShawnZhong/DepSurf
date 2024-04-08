import logging
from collections import defaultdict

from .kind import Kind
from .raw import load_btf_json, RawBTF


class BTFNormalizer(RawBTF):
    def __init__(self, raw_types):
        super().__init__(raw_types)

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

    def get_new_list(self, old_list, expand_anon):
        new_list = []

        anon_count = 0
        for elem in old_list:
            t = self.normalize_impl(elem["type_id"])
            is_anon = elem["name"] == "(anon)"

            if is_anon and expand_anon and (t["kind"] in (Kind.STRUCT, Kind.UNION)):
                t = self.get_raw(elem["type_id"])
                sub_list = self.get_new_list(t["members"], expand_anon=True)
                for sub_item in sub_list:
                    sub_item["bits_offset"] += elem["bits_offset"]
                    new_list.append(sub_item)
                continue

            name = elem["name"]
            if is_anon:
                if anon_count > 0:
                    name = f"(anon-{anon_count})"
                anon_count += 1

            new_list.append(
                {
                    "name": name,
                    **{k: v for k, v in elem.items() if k not in ["name", "type_id"]},
                    "type": t,
                }
            )

        return new_list

    def normalize_list(self, elem, recurse):
        for list_key in ["params", "members"]:
            if list_key not in elem:
                continue

            assert len(elem[list_key]) == elem["vlen"]
            del elem["vlen"]

            if recurse:
                expand_anon = list_key == "members"
                elem[list_key] = self.get_new_list(elem[list_key], expand_anon)
            else:
                del elem[list_key]
                if list_key == "members":
                    del elem["size"]

    def normalize_impl(self, type_id, recurse=False):
        if type_id == 0:
            return {"name": "void", "kind": Kind.VOID.value}

        elem = self.get_raw(type_id)

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
    import pickle

    pkl_path = file.with_suffix(".pkl")

    if pkl_path.exists() and not overwrite:
        logging.info(f"Using {pkl_path}")
        return pkl_path

    json_path = file.with_suffix(".json")
    assert json_path.exists()

    with open(json_path) as f:
        data = load_btf_json(json_path)
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

        logging.info(f"Writing {pkl_path}")
        with open(pkl_path, "wb") as f:
            pickle.dump(dict(result_by_kind), f)

    return pkl_path
