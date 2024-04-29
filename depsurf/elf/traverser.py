from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE
from elftools.dwarf.enums import ENUM_DW_TAG

from .description import get_name, get_name_with_inline, get_die_location_impl


@dataclass
class SubroutineEntry:
    external: bool = False
    caller_inline: list = field(default_factory=list)
    caller_func: list = field(default_factory=list)


@dataclass(frozen=True)
class DIEHandler:
    show: bool
    rec: bool
    handle_fn: Callable[[DIE, int], None] = None
    filter_fn: Callable[[DIE], bool] = None


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
}


class Traverser:
    enable_show = False

    def __init__(self, cu: CompileUnit, handler_map: dict[str, DIEHandler]):
        self.cu = cu

        self.top_die = self.cu.get_top_DIE()
        assert self.top_die.tag == "DW_TAG_compile_unit"

        self.path = self.normalize_path(self.top_die.get_full_path())

        self.line_prog = cu.dwarfinfo.line_program_for_CU(cu)
        self.file_entry = self.line_prog.header.file_entry

        self.include_directory = [
            self.normalize_path(b.decode("ascii"))
            for b in self.line_prog.header.include_directory
        ]

        for tag in handler_map:
            assert tag in ENUM_DW_TAG, tag
        self.handler_map = handler_map
        self.num_indent = 0
        self.curr_subprogram = None

    def normalize_path(self, s: str) -> Path:
        d = Path(s)
        if not d.is_absolute():
            assert d.parts[0] in KERNEL_DIR, d
            return d

        d = d.resolve()
        if d.parts[3].startswith("linux-"):
            return Path(*d.parts[4:])
        else:
            assert d.parts[1] == "usr"
            return d

    def traverse(self):
        if not self.enable_show:
            print(f"Traversing {self.path}")
        self.traverse_impl(self.top_die)

    def traverse_impl(self, die: DIE):
        handler = self.handler_map.get(die.tag)
        if handler is None:
            return

        if die.tag == "DW_TAG_subprogram":
            self.curr_subprogram = get_name(die)

        need_indent = False
        if not handler.filter_fn or handler.filter_fn(die):
            if handler.show and self.enable_show:
                name = get_name_with_inline(die)
                tag = die.tag.removeprefix("DW_TAG_").removeprefix("GNU_")
                print(f"{'  ' * self.num_indent}{tag}: {name}", end="")
                need_indent = True
            if handler.handle_fn:
                handler.handle_fn(die, self)
            if handler.show and self.enable_show:
                print()

        if handler.rec:
            if need_indent:
                self.num_indent += 1
            for child in die.iter_children():
                self.traverse_impl(child)
            if need_indent:
                self.num_indent -= 1

    def get_die_location(self, die: DIE):
        return get_die_location_impl(die, self.file_entry, self.include_directory)
