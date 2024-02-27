from pathlib import Path

from .btf_kind import Kind
from .btf_normalize import read_jsonl


class BTF:
    def __init__(self, path):
        self.path = Path(path)
        self.data = read_jsonl(self.path)
        self.data_by_kind = {}

    def print(self):
        from collections import defaultdict

        print(f"File: {self.path}")

        kinds = defaultdict(int)
        print("Sample:")
        for e in self.data:
            if e["kind"] not in kinds:
                print(f"\t{e['kind']:10}: {e}")
            kinds[e["kind"]] += 1

        kinds = sorted(kinds.items(), key=lambda x: x[1], reverse=True)
        print(f"Kinds: {dict(kinds)}")

        print()

    def filter(self, kind, name_filter=None):
        if kind not in self.data_by_kind:
            self.data_by_kind[kind] = {
                e["name"]: e
                for e in self.data
                if e["kind"] == kind and e["name"] != "(anon)"
            }
        if not name_filter:
            return self.data_by_kind[kind]
        else:
            return {k: v for k, v in self.data_by_kind[kind].items() if name_filter(k)}

    def get(self, arg1, arg2=None):
        if isinstance(arg1, Kind):
            kind = arg1
            name = arg2
            assert name, "Name must be provided"
        elif isinstance(arg1, tuple):
            kind, name = arg1
        else:
            raise ValueError(f"Invalid arguments: {arg1}, {arg2}")
        return self.filter(kind)[name]
