from typing import List, Set
import logging

from .func_entry import FuncEntry
from .enums import CollisionType, InlineType


class FuncGroup:
    def __init__(self, funcs: List[FuncEntry]):
        self.funcs = funcs

    @property
    def name(self):
        return self.funcs[0].name

    @property
    def num_funcs(self):
        return len(self.funcs)

    @property
    def same_loc(self):
        return len({func.loc for func in self.funcs}) == 1

    @property
    def all_static(self):
        return all(not func.external for func in self.funcs)

    def get_collision_type(self) -> CollisionType:
        if self.num_funcs == 1:
            if self.funcs[0].external:
                return CollisionType.UNIQUE_GLOBAL
            else:
                return CollisionType.UNIQUE_STATIC

        # Those are the functions that are declared in single header
        # but defined in multiple files
        if self.same_loc:
            return CollisionType.INCLUDE

        if self.all_static:
            # Static functions have name collision with other static functions
            return CollisionType.STATIC
        else:
            # External functions have name collision with static functions
            return CollisionType.MIXED

    @property
    def any_inline(self):
        return any(func.inline_actual for func in self.funcs)

    @property
    def any_func_caller(self):
        return any(func.has_func_caller for func in self.funcs)

    def get_inline_type(self, in_symtab: bool) -> InlineType:
        name = self.name

        for func in self.funcs:
            if func.has_inline_caller:
                # having inline caller must implies inline
                if not func.inline_actual:
                    logging.warning(
                        f"{name} at {func.loc} has inline caller but not inline."
                    )
            else:
                # if the function is inlined, there could be inline caller miss-counted
                if func.inline_actual:
                    logging.debug(
                        f"{name} at {func.loc} is inline but has no inline caller. "
                        f"maybe it is declared w/ __attribute__((always_inline))"
                    )

        if not in_symtab:
            if self.any_func_caller:
                logging.warning(f"{name} has func caller but no sym entry. ")
            return InlineType.FULL

        if self.any_inline:
            return InlineType.PARTIAL
        else:
            return InlineType.NOT

    def add_func(self, func: FuncEntry):
        if self.num_funcs != 0:
            # All functions in the group should have the same name
            assert self.name == func.name
            if func.external:
                # There should be at most one external function
                assert all(not func.external for func in self.funcs)
        self.funcs.append(func)

    def print(self, file=None):
        loc = self.funcs[0].loc if self.same_loc else None
        header = f"{self.name}"
        if self.num_funcs > 1:
            header += f" ({self.num_funcs})"
        if loc:
            header += f" at {loc}"
        print(header, file=file)
        for func in self.funcs:
            line = f"  {func.file}"
            if not loc:
                line += f" at {func.loc}"
            line += " (global)" if func.external else " (static)"
            line += " (inline)" if func.inline_actual else " (not inline)"
            print(line, file=file)

    def __getitem__(self, index):
        return self.funcs[index]
