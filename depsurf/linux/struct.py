from depsurf.btf import BTF, Kind

from .filebytes import FileBytes


class StructInstance:
    def __init__(self, btf: BTF, filebytes: FileBytes, name: str, ptr: int):
        self.btf = btf
        self.filebytes = filebytes
        self.name = name
        self.ptr = ptr

        t = self.btf.get_struct(name)
        assert t is not None, f"Could not find struct {name}"

        self.size = t["size"]
        self.members = {m["name"]: m for m in t["members"]}

    def get_offset(self, member_name):
        bits_offset = self.members[member_name]["bits_offset"]
        assert bits_offset % 8 == 0
        return bits_offset // 8

    def get(self, name, size=None) -> int:
        m = self.members[name]
        t = m["type"]
        kind = t["kind"]

        addr = self.ptr + self.get_offset(name)

        if size is None:
            if kind == Kind.PTR:
                size = self.filebytes.ptr_size
            elif kind == Kind.INT:
                size = self.btf.data[Kind.INT][t["name"]]["size"]
            else:
                raise NotImplementedError

        return self.filebytes.get_int(addr, size)

    def __getitem__(self, name) -> int:
        return self.get(name)

    def get_bytes(self):
        return self.filebytes.get_bytes(self.ptr, self.size)

    def __repr__(self):
        return f"StructInstance({self.name}, {self.ptr:x}): {self.get_bytes().hex()}"
