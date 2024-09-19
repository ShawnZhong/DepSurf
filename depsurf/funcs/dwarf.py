import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from elftools.dwarf.die import DIE
from elftools.dwarf.enums import ENUM_DW_TAG


KERNEL_DIR = {
    "arch",
    "block",
    "certs",
    "crypto",
    "drivers",
    "fs",
    "include",
    "init",
    "kernel",
    "lib",
    "mm",
    "net",
    "security",
    "sound",
    "virt",
    "rust",
}

def get_name(die: DIE):
    name = die.attributes.get("DW_AT_name")
    if name is None:
        return None
    return name.value.decode("ascii")


def normalize_compile_path(s: str) -> str:
    d = Path(s)
    if not d.is_absolute():
        if d.parts[0] not in KERNEL_DIR:
            logging.warning(f"Suspicious path {d}")
        return str(d)

    d = d.resolve()
    if len(d.parts) >= 4 and d.parts[3].startswith("linux-"):
        return str(Path(*d.parts[4:]))
    else:
        if d.parts[1] not in ("usr", "tmp"):
            logging.warning(f"Suspicious path {d}")
        return str(d)


@dataclass(frozen=True)
class DIEHandler:
    rec: bool
    fn: Callable[[DIE, int], None] = None


class Traverser:
    def __init__(self, top_die: DIE, handler_map: dict[str, DIEHandler]):
        assert top_die.tag == "DW_TAG_compile_unit"
        self.top_die = top_die

        for tag in handler_map:
            assert tag in ENUM_DW_TAG, tag
        self.handler_map = handler_map

        self.path = normalize_compile_path(self.top_die.get_full_path())
        self.lang = self.top_die.attributes["DW_AT_language"].value

        line_prog = top_die.dwarfinfo.line_program_for_CU(top_die.cu)
        self.version = line_prog.header.version
        self.file_entry = line_prog.header.file_entry
        self.include_directory = [
            normalize_compile_path(b.decode("ascii"))
            for b in line_prog.header.include_directory
        ]

        self.num_indent = 0

    def traverse(self):
        self.traverse_impl(self.top_die)

    def traverse_impl(self, die: DIE):
        handler = self.handler_map.get(die.tag)
        if handler is None:
            return

        if handler.fn:
            handler.fn(die, self)

        if handler.rec:
            for child in die.iter_children():
                self.traverse_impl(child)

    def traverse_debug(self):
        self.traverse_debug_impl(self.top_die)

    def traverse_debug_impl(self, die: DIE):
        tag = die.tag

        handler = self.handler_map.get(tag)
        if handler is None:
            return

        if handler.fn:
            handler.fn(die, self)

        name = get_name(die)
        external = die.attributes.get("DW_AT_external")
        if external is not None and external.value == 1:
            assert name is not None
            name += " (external)"
        if "DW_AT_abstract_origin" in die.attributes:
            die_ao = die.get_DIE_from_attribute("DW_AT_abstract_origin")
            die_ao_name = get_name(die_ao) or "<unknown>"
            assert name is None
            name = f"-> {die_ao.offset:#010x} ({die_ao_name})"
        if "DW_AT_call_origin" in die.attributes:
            die_co = die.get_DIE_from_attribute("DW_AT_call_origin")
            die_co_name = get_name(die_co) or "<unknown>"
            assert name is None
            name = f"-> {die_co.offset:#010x} ({die_co_name})"
        tag = tag.removeprefix("DW_TAG_").removeprefix("GNU_")
        print(f"{die.offset:#010x} {'  ' * self.num_indent}{tag} {name or ''}")

        if handler.rec:
            self.num_indent += 1
            for child in die.iter_children():
                self.traverse_debug_impl(child)
            self.num_indent -= 1

    def get_decl_location(self, die: DIE):
        if "DW_AT_decl_file" not in die.attributes:
            if self.lang not in [0x8001]:
                logging.warning(f"Die at {die.offset:#x} does not have DW_AT_decl_file")
            return self.path

        file_idx = die.attributes["DW_AT_decl_file"].value
        if self.version < 5:
            file_idx -= 1

        entry = self.file_entry[file_idx]

        dir_idx = entry.dir_index
        if self.version < 5:
            dir_idx -= 1

        directory = self.include_directory[dir_idx]
        name = entry.name.decode("ascii")

        # return f"{directory}/{name}"

        line = die.attributes["DW_AT_decl_line"].value
        # column = die.attributes["DW_AT_decl_column"].value
        return f"{directory}/{name}:{line}"
