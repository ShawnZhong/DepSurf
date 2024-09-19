import dataclasses
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


class InlineStatus:
    NOT_DECL_NOT_INLINE = 0
    NOT_DECL_INLINE = 1
    DECL_NOT_INLINE = 2
    DECL_INLINE = 3
    NOT_SEEN = -1
    SEEN = -2


@dataclass
class FuncEntry:
    addr: int
    name: str
    external: bool
    loc: Optional[str] = None
    file: Optional[str] = None
    inline: InlineStatus = InlineStatus.NOT_SEEN
    caller_inline: List[Tuple[str, str]] = dataclasses.field(default_factory=list)
    caller_func: List[Tuple[str, str]] = dataclasses.field(default_factory=list)

    @classmethod
    def from_json(cls, s: str):
        return cls(**json.loads(s))

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self))

    @property
    def inline_declared(self) -> bool:
        return self.inline in (InlineStatus.DECL_NOT_INLINE, InlineStatus.DECL_INLINE)

    @property
    def inline_actual(self) -> bool:
        return self.inline in (InlineStatus.NOT_DECL_INLINE, InlineStatus.DECL_INLINE)

    @property
    def inline_str(self) -> str:
        return {
            -2: "not seen",
            -1: "not declared and not inlined",
            0: "not declared and not inlined",
            1: "not declared, but inlined",
            2: "declared, but not inlined",
            3: "declared and inlined",
        }[self.inline]

    @property
    def has_inline_caller(self) -> bool:
        return bool(self.caller_inline)

    @property
    def has_func_caller(self) -> bool:
        return bool(self.caller_func)

    def print_long(self, file=None):
        lines = (
            f"{self.name}",
            f"\tLoc: {self.loc}",
            f"\tFile: {self.file}",
            f"\tInline: {self.inline_str}",
            f"\tExternal: {self.external}",
            f"\tCaller Inline ({len(self.caller_inline)})",
            *(f"\t\t{caller}" for caller in self.caller_inline),
            f"\tCaller Func ({len(self.caller_func)})",
            *(f"\t\t{caller}" for caller in self.caller_func),
        )
        print("\n".join(lines), file=file)

    def print_short(self, file=None, nindent=0):
        indent = "\t" * nindent
        print(
            f"{indent}FuncEntry("
            f"addr={hex(self.addr)}, "
            f"name={self.name}, "
            f"loc={self.loc}, "
            f"file={self.file}, "
            f"external={self.external}, "
            f"caller_func={self.caller_func}, "
            f"caller_inline={self.caller_inline}, "
            f"inline={self.inline}"
            f")",
            file=file,
        )
