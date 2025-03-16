import dataclasses
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, List

from depsurf.issues import IssueEnum

from .entry import FuncEntry
from .symbol import FuncSymbol


class CollisionType(StrEnum):
    UNIQUE_GLOBAL = "Unique Global"
    UNIQUE_STATIC = "Unique Static"
    INCLUDE_DUP = "Static Duplication"
    STATIC_STATIC = "Static-Static Collision"
    STATIC_GLOBAL = "Static-Global Collision"


def get_collision_type(funcs: List[FuncEntry]) -> CollisionType:
    if len(funcs) == 1:
        if funcs[0].external:
            return CollisionType.UNIQUE_GLOBAL
        else:
            return CollisionType.UNIQUE_STATIC

    # Functions with the same location
    # => defined in the header file and included in multiple source files
    if len({func.loc for func in funcs}) == 1:
        return CollisionType.INCLUDE_DUP

    if all(not func.external for func in funcs):
        # Static functions have name collision with other static functions
        return CollisionType.STATIC_STATIC
    else:
        # External functions have name collision with static functions
        return CollisionType.STATIC_GLOBAL


class InlineType(StrEnum):
    NO = "No"
    FULL = "Full"
    SELECTIVE = "Selective"


def get_inline_type(funcs: List[FuncEntry], in_symtab: bool) -> InlineType:
    name = funcs[0].name

    for func in funcs:
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
        # Check if any one of the functions has func caller
        # This case should be very rare
        if any(func.has_func_caller for func in funcs):
            if name.startswith("__builtin_") or name.startswith("__real_"):
                logging.debug(f"{name} is a builtin function")
            elif name in {
                "__switch_to_asm",
                "asm_call_irq_on_stack",
                "asm_call_sysvec_on_stack",
                "relocate_kernel",
                "restore_image",
                "rewind_stack_and_make_dead",
                "rewind_stack_do_exit",
                "soft_restart_cpu",
                "start_cpu0",
                "swsusp_arch_suspend",
                "xen_cpu_bringup_again",
                "xen_pvh_early_cpu_init",
                "__efi64_thunk",
            }:
                logging.debug(f"{name} is an assembly function")
            elif name.startswith("efi_"):
                logging.debug(f"{name} is an EFI function")
            else:
                logging.warning(f"{name} has func caller but no sym entry. ")
        return InlineType.FULL

    if any(func.inline_actual for func in funcs):
        # Any of the functions is inlined
        return InlineType.SELECTIVE
    else:
        return InlineType.NO


@dataclass(frozen=True)
class FuncGroup:
    name: str
    collision_type: CollisionType
    inline_type: InlineType
    funcs: List[FuncEntry]
    symbols: List[FuncSymbol]

    @classmethod
    def from_funcs(cls, funcs: List[FuncEntry], symbols: List[FuncSymbol]):
        assert len(funcs) > 0, "There must be at least one function in a group"
        assert all(func.name == funcs[0].name for func in funcs), (
            "All functions must have the same name"
        )
        assert sum(func.external for func in funcs) <= 1, (
            "There should be at most one external function in a group"
        )

        return cls(
            name=funcs[0].name,
            collision_type=get_collision_type(funcs),
            inline_type=get_inline_type(funcs, len(symbols) > 0),
            funcs=funcs,
            symbols=symbols,
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "FuncGroup":
        return cls(
            name=data["name"],
            funcs=[FuncEntry(**func) for func in data["funcs"]],
            collision_type=CollisionType(data["collision_type"]),
            inline_type=InlineType(data["inline_type"]),
            symbols=[FuncSymbol(**sym) for sym in data["symbols"]],
        )

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)

    @property
    def num_funcs(self):
        return len(self.funcs)

    @property
    def has_suffix(self):
        return any(sym.has_suffix for sym in self.symbols)

    @property
    def issues(self) -> List[IssueEnum]:
        result = []

        # collision
        if self.collision_type == CollisionType.INCLUDE_DUP:
            result.append(IssueEnum.DUPLICATE)
        elif self.collision_type in (
            CollisionType.STATIC_STATIC,
            CollisionType.STATIC_GLOBAL,
        ):
            result.append(IssueEnum.COLLISION)

        # inline
        if self.inline_type == InlineType.FULL:
            result.append(IssueEnum.FULL_INLINE)
        elif self.inline_type == InlineType.SELECTIVE:
            result.append(IssueEnum.SELECTIVE_INLINE)

        # transformation
        if self.has_suffix:
            result.append(IssueEnum.TRANSFORMATION)

        return result

    def __getitem__(self, index):
        return self.funcs[index]

    def __iter__(self):
        return iter(self.funcs)
