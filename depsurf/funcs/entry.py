import dataclasses
import json
from dataclasses import dataclass
from typing import List, Optional
from enum import StrEnum


class InlineStatus(StrEnum):
    NOT_DECL_NOT_INLINE = "not declared, not inlined"
    NOT_DECL_INLINE = "not declared, inlined"
    DECL_NOT_INLINE = "declared, not inlined"
    DECL_INLINE = "declared, inlined"
    UNSEEN = "not seen"
    SEEN_UNKNOWN = "seen, unknown"

    @classmethod
    def from_num(cls, n: int) -> "InlineStatus":
        return [
            cls.NOT_DECL_NOT_INLINE,
            cls.NOT_DECL_INLINE,
            cls.DECL_NOT_INLINE,
            cls.DECL_INLINE,
        ][n]

    @property
    def num(self) -> int:
        return {
            self.NOT_DECL_NOT_INLINE: 0,
            self.NOT_DECL_INLINE: 1,
            self.DECL_NOT_INLINE: 2,
            self.DECL_INLINE: 3,
        }[self]


@dataclass
class FuncEntry:
    addr: int
    name: str
    external: bool
    loc: Optional[str] = None
    file: Optional[str] = None
    inline: InlineStatus = InlineStatus.UNSEEN
    caller_inline: List[str] = dataclasses.field(default_factory=list)
    caller_func: List[str] = dataclasses.field(default_factory=list)

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
    def has_inline_caller(self) -> bool:
        return bool(self.caller_inline)

    @property
    def has_func_caller(self) -> bool:
        return bool(self.caller_func)
