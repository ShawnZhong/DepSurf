from typing import Dict, Tuple

from depsurf.issues import IssueEnum


class BaseChange:
    def __init_subclass__(cls, enum: IssueEnum):
        cls.enum = enum

    def format(self):
        return ""

    def print(self, file=None, nindent=0):
        indent = "\t" * nindent
        format = self.format()
        if format:
            print(f"{indent}{self.enum:24}{format}", file=file)
        else:
            print(f"{indent}{self.enum}", file=file)


def diff_dict(
    old: Dict, new: Dict
) -> Tuple[Dict[str, Dict], Dict[str, Dict], Dict[str, Tuple[Dict, Dict]]]:
    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    common = {k: (old[k], new[k]) for k in old.keys() if k in new}
    return added, removed, common
