import dataclasses
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE
from elftools.dwarf.dwarfinfo import DWARFInfo
from elftools.elf.elffile import ELFFile

from depsurf.utils import manage_result_path

from .dwarf import DIEHandler, Traverser, get_name
from .entry import FuncEntry, InlineStatus


def get_pc(die: DIE) -> int:
    attrs = ["DW_AT_low_pc", "DW_AT_entry_pc", "DW_AT_high_pc"]
    for attr in attrs:
        val = die.attributes.get(attr)
        if val is not None:
            return val.value
    return 0


class FunctionRecorder:
    def __init__(self):
        self.data: Dict[str, Dict[Tuple[Optional[str], Optional[str]], FuncEntry]] = {}
        self.curr_prog = None

    def iter_funcs(self):
        for name, group in self.data.items():
            for loc, func in group.items():
                if func.name.startswith("__compiletime_assert_"):
                    continue
                yield func

    def get_or_create_entry(self, die: DIE, traverser: Traverser) -> FuncEntry:
        name = get_name(die)
        assert name is not None, f"{die.offset:#x}"

        group = self.data.setdefault(name, {})

        external = die.attributes.get("DW_AT_external")
        external = False if external is None else external.value == 1

        if external:
            (loc, file) = (None, None)
        else:
            loc = traverser.get_decl_location(die)
            file = traverser.path

        key = (loc, file)

        entry = group.get(key)
        if entry is not None:
            return entry

        entry = FuncEntry(
            addr=0,
            name=name,
            external=external,
            loc=loc,
            file=file,
        )
        group[key] = entry

        return entry

    def record_prog(self, die: DIE, traverser: Traverser):
        assert die.tag == "DW_TAG_subprogram"

        # ignore inlined subprograms as they will be accounted at the call site
        if "DW_AT_abstract_origin" in die.attributes:
            assert "DW_AT_inline" not in die.attributes
            assert "DW_AT_name" not in die.attributes
            self.curr_prog = None
            origin_die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
            entry = self.get_or_create_entry(origin_die, traverser)
            if entry.addr == 0:
                entry.addr = get_pc(die)
            return

        entry = self.get_or_create_entry(die, traverser)

        decl = die.attributes.get("DW_AT_declaration")
        decl = False if decl is None else decl.value == 1
        if decl:
            # declaration-only subprograms
            return

        self.curr_prog = entry.name

        # set inline attribute
        inline = die.attributes.get("DW_AT_inline")
        if entry.inline in (InlineStatus.UNSEEN, InlineStatus.SEEN_UNKNOWN):
            if inline is not None:
                entry.inline = InlineStatus.from_num(inline.value)
            else:
                entry.inline = InlineStatus.SEEN_UNKNOWN
        else:
            if inline is not None and entry.inline.num != inline.value:
                logging.warning(
                    f"Conflicting inline status: {entry.inline} vs {inline.value} at {die.offset:#x}"
                )

        if entry.loc is None:
            entry.loc = traverser.get_decl_location(die)
        if entry.file is None:
            entry.file = traverser.path

        if entry.addr == 0:
            entry.addr = get_pc(die)

    def record_call_gnu(self, die: DIE, traverser: Traverser):
        if "DW_AT_abstract_origin" not in die.attributes:
            return  # indirect call
        die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
        if "DW_AT_abstract_origin" in die.attributes:
            die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
        self.record_call_impl(die, traverser, is_inline=False)

    def record_call(self, die: DIE, traverser: Traverser):
        if "DW_AT_call_origin" not in die.attributes:
            return  # indirect call
        die = die.get_DIE_from_attribute("DW_AT_call_origin")
        if "DW_AT_abstract_origin" in die.attributes:
            die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
        self.record_call_impl(die, traverser, is_inline=False)

    def record_inline(self, die: DIE, traverser: Traverser):
        fn_die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
        entry = self.record_call_impl(fn_die, traverser, is_inline=True)
        if entry.addr == 0:
            entry.addr = get_pc(die)

    def record_call_impl(self, die: DIE, traverser: Traverser, is_inline: bool):
        entry = self.get_or_create_entry(die, traverser)

        caller_name = self.curr_prog
        # this may happen when a subprogram has abstract_origin
        if caller_name is None:
            return entry

        caller_loc = f"{traverser.path}:{caller_name}"

        if is_inline:
            assert entry.name != caller_name, f"{entry.addr:#x}"
            entry.caller_inline.append(caller_loc)
        else:
            # it is possible that entry.name == caller_name (e.g., recursive call)
            entry.caller_func.append(caller_loc)

        return entry

    @classmethod
    def from_cus(cls, cus: List[CompileUnit], debug=False):
        obj = cls()
        handler_map = {
            "DW_TAG_compile_unit": DIEHandler(rec=True),
            "DW_TAG_lexical_block": DIEHandler(rec=True),
            "DW_TAG_subprogram": DIEHandler(rec=True, fn=obj.record_prog),
            "DW_TAG_inlined_subroutine": DIEHandler(rec=True, fn=obj.record_inline),
            # We don't want to recurse into call sites to avoid double counting
            "DW_TAG_GNU_call_site": DIEHandler(rec=False, fn=obj.record_call_gnu),
            "DW_TAG_call_site": DIEHandler(rec=False, fn=obj.record_call),
        }

        cus = list(cus)
        for i, cu in enumerate(cus):
            top_die = cu.get_top_DIE()
            lang = top_die.attributes["DW_AT_language"].value
            if lang == 0x001C:  #  # ignore DW_LANG_Rust
                logging.info(f"Ignoring {i + 1}/{len(cus)}: {traverser.path}")
                continue

            traverser = Traverser(top_die, handler_map)
            logging.debug(f"Traversing {i + 1}/{len(cus)}: {traverser.path}")
            if debug:
                traverser.traverse_debug()
            else:
                traverser.traverse()

        return obj

    @classmethod
    def from_path(cls, path: Path, cus_mapper=None, debug=False):
        logging.info(f"Dumping functions from {path}")
        with path.open("rb") as f:
            elffile = ELFFile(f)
            dwarfinfo = elffile.get_dwarf_info(relocate_dwarf_sections=False)
            cus = dwarfinfo.iter_CUs()
            if cus_mapper is not None:
                cus = cus_mapper(cus)
            obj = cls.from_cus(cus, debug=debug)
            del dwarfinfo
            del elffile
        return obj

    def dump(self, path: Path):
        with open(path, "w") as f:
            for func in self.iter_funcs():
                print(json.dumps(dataclasses.asdict(func)), file=f)


def disable_dwarf_cache():
    def _get_cached_DIE(self: CompileUnit, offset):
        top_die_stream = self.get_top_DIE().stream
        return DIE(cu=self, stream=top_die_stream, offset=offset)

    CompileUnit._get_cached_DIE = _get_cached_DIE
    DWARFInfo._cached_CU_at_offset = DWARFInfo._parse_CU_at_offset


@manage_result_path
def dump_func_entries(path: Path, result_path: Path):
    disable_dwarf_cache()

    FunctionRecorder.from_path(path).dump(result_path)
