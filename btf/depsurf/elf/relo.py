from dataclasses import dataclass
from enum import Enum
from pprint import pformat
from typing import List

from depsurf.btf import dump_btf, load_btf_json
from elftools.elf.elffile import ELFFile

from .objfile import ObjectFile
from .structs import (
    bpf_core_relo_t,
    btf_ext_header_t,
    btf_ext_info_sec_t,
    btf_header_t,
    rec_size_t,
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
        end = self.strtab.find(b"\x00", off)
        return self.strtab[off:end].decode()


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


@dataclass
class BTFReloEntry:
    insn_off: int
    types: list
    access_str: str
    kind: BTFCoreReloKind

    def __init__(self, data, strtab: BTFStrtab, btf_types):
        header = bpf_core_relo_t.parse(data)
        self.insn_off = header.insn_off
        self.kind = BTFCoreReloKind(header.kind)

        self.access_str = strtab.get(header.access_str_off)
        access_nums = [int(num) for num in self.access_str.split(":")]

        self.types = []
        assert access_nums[0] == 0
        t = btf_types[header.type_id - 1]
        for num in access_nums[1:]:
            member = t["members"][num]
            self.types.append((t["kind"], t["name"], member["name"]))
            t = btf_types[member["type_id"] - 1]


@dataclass
class BTFReloSection:
    sec_name: str
    relocations: List[BTFReloEntry]

    def __init__(self, data, strtab: BTFStrtab, btf_types):
        header = btf_ext_info_sec_t.parse(data)

        self.sec_name = strtab.get(header.sec_name_off)

        self.relocations = []
        for i in range(header.num_info):
            rec = data[self.get_off(i) : self.get_off(i + 1)]
            self.relocations.append(BTFReloEntry(rec, strtab, btf_types))

    def get_off(self, i):
        return btf_ext_info_sec_t.sizeof() + i * bpf_core_relo_t.sizeof()

    @property
    def size(self):
        return self.get_off(len(self.relocations))


@dataclass
class BTFReloInfo:
    relo_sections: List[BTFReloSection]

    def __init__(self, data, strtab: BTFStrtab, btf_types):
        assert rec_size_t.parse(data) == bpf_core_relo_t.sizeof()
        data = data[rec_size_t.sizeof() :]

        self.relo_sections = []
        while len(data) > 0:
            sec = BTFReloSection(data, strtab, btf_types)
            self.relo_sections.append(sec)
            data = data[sec.size :]

    def __repr__(self):
        return pformat(self.relo_sections, sort_dicts=False)


class BPFObjectFile(ObjectFile):
    def __init__(self, path):
        super().__init__(path)

        self.strtab = BTFStrtab(self.elf)

        btf_ext = self.elf.get_section_by_name(".BTF.ext")
        header = btf_ext_header_t.parse(btf_ext.data())

        def get_slice(off, size):
            off += header.hdr_len
            return btf_ext.data()[off : off + size]

        self.func_info = get_slice(header.func_info_off, header.func_info_len)
        self.line_info = get_slice(header.line_info_off, header.line_info_len)
        self.core_relo = get_slice(header.core_relo_off, header.core_relo_len)

        self.btf_types = None

    def get_relo_info(self):
        if self.btf_types is None:
            dump_btf(self.path, overwrite=True)
            self.btf_types = load_btf_json(self.path.with_suffix(".json"))

        return BTFReloInfo(self.core_relo, self.strtab, self.btf_types)
