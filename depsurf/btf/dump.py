import json
import logging
from functools import cached_property
from pathlib import Path
from typing import Dict

from depsurf.utils import manage_result_path

from .kind import Kind


class BTFNormalizer:
    def __init__(self, path: Path):
        assert path.suffix == ".json"
        self.path = path

    @cached_property
    def raw_types(self):
        with open(self.path) as f:
            return json.load(f)["types"]

    def get_raw(self, type_id):
        elem = self.raw_types[type_id - 1]
        assert elem["id"] == type_id
        return elem

    RECURSE_KINDS = {
        Kind.CONST,
        Kind.VOLATILE,
        Kind.RESTRICT,
        Kind.PTR,
        Kind.FUNC,
        Kind.FUNC_PROTO,
        Kind.ARRAY,
    }

    def normalize_int(self, elem, recurse):
        assert elem["bits_offset"] == 0
        del elem["bits_offset"]
        del elem["encoding"]
        del elem["nr_bits"]
        if not recurse:
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
                elem[type_key] = self.normalize(elem[type_id], recurse=False)
            del elem[type_id]

    def get_new_list(self, old_list, expand_anon):
        new_list = []

        anon_count = 0
        for elem in old_list:
            t = self.normalize(elem["type_id"], recurse=False)
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

    def normalize(self, type_id, recurse):
        if type_id == 0:
            return {"name": "void", "kind": Kind.VOID.value}

        elem = self.get_raw(type_id)

        kind = elem["kind"]

        # Recurse into types for certain kinds
        recurse = recurse or kind in self.RECURSE_KINDS

        elem = elem.copy()

        del elem["id"]

        if kind == Kind.INT:
            self.normalize_int(elem, recurse)
        elif kind == Kind.ARRAY:
            del elem["index_type_id"]
        elif kind in (Kind.ENUM, Kind.ENUM64):
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

    @cached_property
    def data(self):
        logging.info(f"Normalizing types from {self.path}")
        results: Dict[str, Dict[str, Dict]] = {k.value: {} for k in Kind}

        anon_enum_values = []
        for i in range(1, len(self.raw_types) + 1):
            t = self.normalize(i, recurse=True)

            name = t.get("name")
            if name is None:
                continue

            if name == "(anon)":
                if t["kind"] == Kind.ENUM.value:
                    anon_enum_values += t["values"]
                continue

            kind = t["kind"]
            group = results.get(kind)
            if group is None:
                results[kind] = {name: t}
            else:
                if name in group:
                    logging.debug(f"Duplicate type {name}")
                else:
                    group[name] = t

        if anon_enum_values:
            results[Kind.ENUM.value]["(anon)"] = {
                "kind": "ENUM",
                "name": "(anon)",
                "size": 4,
                "values": anon_enum_values,
            }
        return results

    @manage_result_path
    def dump_types(self, kind: Kind, result_path: Path):
        with open(result_path, "w") as f:
            for k, v in self.data[kind].items():
                print(json.dumps(v), file=f)


def dump_types(btf_json_path: Path, result_paths: Dict[Kind, Path], overwrite: bool = False):
    normalizer = BTFNormalizer(btf_json_path)
    for kind, path in result_paths.items():
        normalizer.dump_types(kind, result_path=path, overwrite=overwrite)
