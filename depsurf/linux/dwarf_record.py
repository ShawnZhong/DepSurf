import logging
from pathlib import Path
from typing import List

from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile

from .dwarf_funcs import FuncEntry, FunctionGroups
from .dwarf_traverse import DIEHandler, Traverser, get_name


class FunctionRecorder:
    def __init__(self):
        self.data: FunctionGroups = FunctionGroups({})
        self.curr_prog = None

    def get_or_create_entry(self, die: DIE, traverser: Traverser) -> FuncEntry:
        name = get_name(die)
        assert name is not None, f"{die.offset:#x}"

        loc_dict = self.data.get_or_create_group(name)

        external = die.attributes.get("DW_AT_external")
        external = False if external is None else external.value == 1

        if external:
            (decl_loc, file) = (None, None)
        else:
            decl_loc = traverser.get_decl_location(die)
            file = traverser.path

        key = (decl_loc, file)

        entry = loc_dict.get(key)
        if entry is not None:
            return entry

        entry = FuncEntry(
            name=name,
            external=external,
            decl_loc=decl_loc,
            file=file,
        )
        loc_dict[key] = entry

        return entry

    def record_prog(self, die: DIE, traverser: Traverser):
        assert die.tag == "DW_TAG_subprogram"

        # ignore inlined subprograms as they will be accounted at the call site
        if "DW_AT_abstract_origin" in die.attributes:
            assert "DW_AT_inline" not in die.attributes
            assert "DW_AT_name" not in die.attributes
            self.curr_prog = None
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
        entry.inline = inline.value if inline is not None else 0

        if entry.decl_loc is None and entry.file is None:
            entry.decl_loc = traverser.get_decl_location(die)
            entry.file = traverser.path

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
        die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
        self.record_call_impl(die, traverser, is_inline=True)

    def record_call_impl(self, die: DIE, traverser: Traverser, is_inline: bool):
        entry = self.get_or_create_entry(die, traverser)

        # this may happen when a subprogram has abstract_origin
        if self.curr_prog is None:
            return

        if is_inline:
            assert entry.name != self.curr_prog, f"{entry.offset:#x}"
            entry.caller_inline.append(self.curr_prog)
        else:
            # it is possible that entry.name == self.curr_prog (e.g., recursive call)
            entry.caller_func.append(self.curr_prog)

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
                logging.info(f"Ignoring {i+1}/{len(cus)}: {traverser.path}")
                continue

            traverser = Traverser(top_die, handler_map)
            logging.info(f"Traversing {i+1}/{len(cus)}: {traverser.path}")
            if debug:
                traverser.traverse_debug()
            else:
                traverser.traverse()

        return obj

    @classmethod
    def from_path(cls, path: Path, cus_mapper=None, debug=False):
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
