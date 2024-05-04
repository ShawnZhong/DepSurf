import dataclasses
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple


class InlineStatus:
    NOT_DECL_NOT_INLINE = 0
    NOT_DECL_INLINE = 1
    DECL_NOT_INLINE = 2
    DECL_INLINE = 3
    NOT_SEEN = -1
    SEEN = -2


@dataclass
class FuncEntry:
    name: str
    external: bool
    inline: InlineStatus = InlineStatus.NOT_SEEN
    loc: str = None
    file: str = None
    caller_inline: List[Tuple[str, str]] = dataclasses.field(default_factory=list)
    caller_func: List[Tuple[str, str]] = dataclasses.field(default_factory=list)

    @classmethod
    def from_json(cls, s: str):
        return cls(**json.loads(s))

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @property
    def inline_declared(self) -> bool:
        return self.inline in (InlineStatus.DECL_NOT_INLINE, InlineStatus.DECL_INLINE)

    @property
    def inline_actual(self) -> bool:
        return self.inline in (InlineStatus.NOT_DECL_INLINE, InlineStatus.DECL_INLINE)

    @property
    def inline_status(self) -> str:
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

    def __str__(self):
        lines = (
            f"{self.name}",
            f"\tLoc: {self.loc}",
            f"\tFile: {self.file}",
            f"\tInline: {self.inline_status}",
            f"\tExternal: {self.external}",
            f"\tCaller Inline ({len(self.caller_inline)})",
            *(f"\t\t{caller}" for caller in self.caller_inline),
            f"\tCaller Func ({len(self.caller_func)})",
            *(f"\t\t{caller}" for caller in self.caller_func),
        )
        return "\n".join(lines)
