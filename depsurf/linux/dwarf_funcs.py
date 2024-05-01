import logging
import dataclasses
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List

from elftools.dwarf.compileunit import CompileUnit
from elftools.dwarf.die import DIE

from .dwarf_traverse import DIEHandler, Traverser, get_name

import pickle


@dataclass
class FuncEntry:
    name: str
    external: bool
    decl_loc: str
    def_loc: str
    inline: int = -1  # 2, 3: declared inline; 1, 3: actually inline
    caller_inline: list = dataclasses.field(default_factory=list)
    caller_func: list = dataclasses.field(default_factory=list)


class Functions:
    def __init__(self):
        # function name -> (location -> FuncEntry)
        self.data: Dict[str, Dict[str, FuncEntry]] = {}
        self.curr_prog = None

    @cached_property
    def df(self):
        import pandas as pd

        df = pd.DataFrame(
            [
                dataclasses.asdict(info)
                for loc_dict in self.data.values()
                for info in loc_dict.values()
            ]
        )
        return df

    def dump(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.data, f)

    @classmethod
    def from_dump(cls, path):
        funcs = cls()
        with open(path, "rb") as f:
            funcs.data = pickle.load(f)
        return funcs

    def get_entry(self, die: DIE, traverser: Traverser):
        name = get_name(die)
        assert name is not None, f"{die.offset:#x}"
        if name is None:
            logging.warning(f"Failed to get entry for {die.offset:#x}")
            return None

        loc_dict = self.data.get(name)
        if loc_dict is None:
            loc_dict = {}
            self.data[name] = loc_dict

        external = die.attributes.get("DW_AT_external")
        external = False if external is None else external.value == 1
        if external:
            (decl_loc, def_loc) = (None, None)
        else:
            decl_loc = traverser.get_decl_location(die)
            def_loc = traverser.path

        key = (decl_loc, def_loc)

        entry = loc_dict.get(key)
        if entry is not None:
            return entry

        entry = FuncEntry(
            name=name,
            external=external is not None,
            decl_loc=decl_loc,
            def_loc=def_loc,
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

        entry = self.get_entry(die, traverser)
        if entry is None:
            logging.warning(f"Failed to get entry for {die.offset:#x}")
            return

        # ignore declarations for inline attribute
        decl = die.attributes.get("DW_AT_declaration")
        if decl is not None:
            assert decl.value == 1
            return

        self.curr_prog = entry.name

        # set inline attribute
        inline = die.attributes.get("DW_AT_inline")
        entry.inline = inline.value if inline is not None else 0

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
        entry = self.get_entry(die, traverser)
        if entry is None:
            return

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
        funcs = cls()
        handler_map = {
            "DW_TAG_compile_unit": DIEHandler(rec=True),
            "DW_TAG_lexical_block": DIEHandler(rec=True),
            "DW_TAG_subprogram": DIEHandler(rec=True, fn=funcs.record_prog),
            "DW_TAG_inlined_subroutine": DIEHandler(rec=True, fn=funcs.record_inline),
            # We don't want to recurse into call sites to avoid double counting
            "DW_TAG_GNU_call_site": DIEHandler(rec=False, fn=funcs.record_call_gnu),
            "DW_TAG_call_site": DIEHandler(rec=False, fn=funcs.record_call),
        }

        cus = list(cus)
        for i, cu in enumerate(cus):
            traverser = Traverser(cu, handler_map)
            logging.info(f"Traversing {i+1}/{len(cus)}: {traverser.path}")
            if debug:
                traverser.traverse_debug()
            else:
                traverser.traverse()

        return funcs

    @classmethod
    def from_dwarfinfo(cls, dwarfinfo):
        cus = list(dwarfinfo.iter_CUs())
        return cls.from_cus(cus)
