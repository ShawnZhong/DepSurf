from typing import TYPE_CHECKING

from depsurf.btf import Kind

if TYPE_CHECKING:
    from .image import LinuxImage


class StructInstance:
    def __init__(self, img: "LinuxImage", name: str, ptr: int):
        self.img = img
        self.name = name
        self.ptr = ptr

        t = img.btf.get_struct(name)
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
                size = self.img.ptr_size
            elif kind == Kind.INT:
                size = self.img.btf.data[Kind.INT][t["name"]]["size"]
            else:
                raise NotImplementedError

        return self.img.get_int(addr, size)

    def __getitem__(self, name) -> int:
        return self.get(name)

    def get_bytes(self):
        return self.img.get_bytes(self.ptr, self.size)

    def __repr__(self):
        return f"StructInstance({self.name}, {self.ptr:x}): {self.get_bytes().hex()}"
