from dataclasses import dataclass
from enum import Enum

from depsurf.btf import Kind, RawBTF
from elftools.construct import Struct, ULInt8, ULInt16, ULInt32
from elftools.elf.elffile import ELFFile

from depsurf.utils import get_cstr

btf_header_t = Struct(
    "btf_header",
    ULInt16("magic"),
    ULInt8("version"),
    ULInt8("flags"),
    ULInt32("hdr_len"),
    # type
    ULInt32("type_off"),
    ULInt32("type_len"),
    # string
    ULInt32("str_off"),
    ULInt32("str_len"),
)

btf_ext_header_t = Struct(
    "btf_ext_header",
    ULInt16("magic"),
    ULInt8("version"),
    ULInt8("flags"),
    ULInt32("hdr_len"),
    # func
    ULInt32("func_info_off"),
    ULInt32("func_info_len"),
    # line
    ULInt32("line_info_off"),
    ULInt32("line_info_len"),
    # core
    ULInt32("core_relo_off"),
    ULInt32("core_relo_len"),
)

rec_size_t = ULInt32("rec_size")

btf_ext_info_sec_t = Struct(
    "btf_ext_info_sec",
    ULInt32("sec_name_off"),
    ULInt32("num_info"),
)

bpf_core_relo_t = Struct(
    "bpf_core_relo",
    ULInt32("insn_off"),
    ULInt32("type_id"),
    ULInt32("access_str_off"),
    ULInt32("kind"),
)


@dataclass
class BTFStrtab:
    strtab: bytes

    def __init__(self, elf: ELFFile):
        btf = elf.get_section_by_name(".BTF")

        data = btf.data()
        header = btf_header_t.parse(data)

        off = header.hdr_len + header.str_off
        self.strtab = data[off : off + header.str_len]

    def get(self, off):
        return get_cstr(self.strtab, off)


class BTFCoreReloKind(Enum):
    FIELD_BYTE_OFFSET = 0  # field byte offset
    FIELD_BYTE_SIZE = 1  # field size in bytes
    FIELD_EXISTS = 2  # field existence in target kernel
    FIELD_SIGNED = 3  # field signedness (0 - unsigned, 1 - signed)
    FIELD_LSHIFT_U64 = 4  # bitfield-specific left bitshift
    FIELD_RSHIFT_U64 = 5  # bitfield-specific right bitshift
    TYPE_ID_LOCAL = 6  # type ID in local BPF object
    TYPE_ID_TARGET = 7  # type ID in target kernel
    TYPE_EXISTS = 8  # type existence in target kernel
    TYPE_SIZE = 9  # type size in bytes
    ENUMVAL_EXISTS = 10  # enum value existence in target kernel
    ENUMVAL_VALUE = 11  # enum value integer value
    TYPE_MATCHES = 12  # type match in target kernel

    @property
    def name(self):
        return {
            BTFCoreReloKind.FIELD_BYTE_OFFSET: "byte_off",
            BTFCoreReloKind.FIELD_BYTE_SIZE: "byte_sz",
            BTFCoreReloKind.FIELD_EXISTS: "field_exists",
            BTFCoreReloKind.FIELD_SIGNED: "signed",
            BTFCoreReloKind.FIELD_LSHIFT_U64: "lshift_u64",
            BTFCoreReloKind.FIELD_RSHIFT_U64: "rshift_u64",
            BTFCoreReloKind.TYPE_ID_LOCAL: "local_type_id",
            BTFCoreReloKind.TYPE_ID_TARGET: "target_type_id",
            BTFCoreReloKind.TYPE_EXISTS: "type_exists",
            BTFCoreReloKind.TYPE_SIZE: "type_size",
            BTFCoreReloKind.ENUMVAL_EXISTS: "enumval_exists",
            BTFCoreReloKind.ENUMVAL_VALUE: "enumval_value",
            BTFCoreReloKind.TYPE_MATCHES: "type_matches",
        }[self]


@dataclass(eq=True, frozen=True, order=True, repr=False)
class Dep:
    kind: Kind
    name: str
    member: str = ""

    @classmethod
    def from_t(cls, t, member=""):
        return cls(t["kind"], t["name"].split("___")[0], member)

    def __repr__(self):
        s = f"{self.kind.lower()} {self.name}"
        if self.member != "":
            s += f"::{self.member}"
        return s


class BTFReloEntry:
    def __init__(self, data, strtab: BTFStrtab, btf_types: RawBTF):
        header = bpf_core_relo_t.parse(data)

        self.insn_off = header.insn_off
        self.type_id = header.type_id
        self.access_str = strtab.get(header.access_str_off)
        self.kind = BTFCoreReloKind(header.kind)
        self.btf_types = btf_types

        t = btf_types.get_raw(header.type_id)
        self.string = f"{Dep.from_t(t)}"

        access_nums = [int(num) for num in self.access_str.split(":")]

        if t["kind"] == Kind.ENUM:
            assert len(access_nums) == 1
            num = access_nums[0]
            value = t["values"][num]
            name = value["name"]
            self.string += f".{name}"
            self.deps = [Dep.from_t(t, name)]
            return

        assert access_nums[0] == 0
        if len(access_nums) == 1:
            self.deps = [Dep.from_t(t)]
            return

        deps = []
        for num in access_nums[1:]:
            t = self.handle(num, t, deps)

        self.deps = self.normalize_deps(deps)

    def normalize_deps(self, deps):
        new_deps = []

        for dep in deps:
            is_type_anon = dep.name == "(anon)"
            is_member_anon = dep.member == "(anon)"

            if is_member_anon and is_type_anon:
                continue

            if is_type_anon:
                new_deps.append(Dep(named_dep.kind, named_dep.name, dep.member))
                named_dep = None
                continue
            else:
                named_dep = dep

            if is_member_anon:
                continue

            new_deps.append(dep)

        return new_deps

    def handle(self, num, t, deps):
        if "members" in t:
            member = t["members"][num]
            name = member["name"]
            self.string += f".{name}"
            deps.append(Dep.from_t(t, name))
            return self.btf_types.get_raw(member["type_id"])
        elif t["kind"] == Kind.ARRAY:
            self.string += f"[{num}]"
            return self.btf_types.get_raw(t["type_id"]), None
        elif t["kind"] == Kind.TYPEDEF:
            deps.append(Dep.from_t(t))
            real_t = self.btf_types.get_raw(t["type_id"])
            return self.handle(num, real_t, deps)

        assert False, f"Unhandled type: {t['kind']}"

    def __repr__(self):
        return f"{self.insn_off:04x}: CO-RE <{self.kind.name}> [{self.type_id}] {self.string} ({self.access_str})\n\t\t deps on {self.deps}"


class BTFReloSection:
    def __init__(self, data, strtab: BTFStrtab, btf_types: RawBTF):
        header = btf_ext_info_sec_t.parse(data)

        self.sec_name = strtab.get(header.sec_name_off)
        self.relocations = [
            BTFReloEntry(data[self.get_off(i) : self.get_off(i + 1)], strtab, btf_types)
            for i in range(header.num_info)
        ]

    def get_off(self, i):
        return btf_ext_info_sec_t.sizeof() + i * bpf_core_relo_t.sizeof()

    @property
    def size(self):
        return self.get_off(len(self.relocations))

    def __repr__(self):
        s = f"Relocation for {self.sec_name}:\n\t"
        s += "\n\t".join(map(str, self.relocations))
        return s


class BTFReloInfo:
    def __init__(self, data, strtab: BTFStrtab, btf_types: RawBTF):
        self.relo_sections = []

        if len(data) == 0:
            return

        assert rec_size_t.parse(data) == bpf_core_relo_t.sizeof()
        data = data[rec_size_t.sizeof() :]
        while len(data) > 0:
            sec = BTFReloSection(data, strtab, btf_types)
            self.relo_sections.append(sec)
            data = data[sec.size :]

    def get_deps(self):
        return sorted(
            {
                dep
                for sec in self.relo_sections
                for relo in sec.relocations
                for dep in relo.deps
            }
        )

    def __repr__(self):
        return "\n".join(map(str, self.relo_sections))


@dataclass
class BTFExtSection:
    func_info: bytes
    line_info: bytes
    relo_info: bytes

    @classmethod
    def from_elf(cls, elf: ELFFile):
        btf_ext = elf.get_section_by_name(".BTF.ext").data()
        header = btf_ext_header_t.parse(btf_ext)

        def get_slice(off, size):
            off += header.hdr_len
            return btf_ext[off : off + size]

        return cls(
            get_slice(header.func_info_off, header.func_info_len),
            get_slice(header.line_info_off, header.line_info_len),
            get_slice(header.core_relo_off, header.core_relo_len),
        )
