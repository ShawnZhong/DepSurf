from typing import List, Tuple

from depsurf.diff import DiffChanges, get_diff_fn
from depsurf.btf import Kind, BTF
from depsurf.cause import GenericChange


class KernelImages:
    def __init__(self, btfs: List[BTF]):
        self.btfs = btfs

    @property
    def all_versions(self):
        return [btf.short_version for btf in self.btfs]

    def __len__(self):
        return len(self.all_versions)

    def get_changes(self, kind, name) -> List[Tuple[str, str, DiffChanges]]:
        result = []
        for btf1, btf2 in zip(self.btfs, self.btfs[1:]):
            t1 = btf1.get(kind, name)
            t2 = btf2.get(kind, name)
            if t1 is None or t2 is None:
                continue
            # if t1 is None and t2 is not None:
            #     c = {
            #         Kind.FUNC: GenericChange.FUNC_ADD,
            #         Kind.STRUCT: GenericChange.STRUCT_ADD,
            #     }[kind]
            #     result.append((btf1.short_version, btf2.short_version, [c]))
            #     continue
            # if t1 is not None and t2 is None:
            #     c = {
            #         Kind.FUNC: GenericChange.FUNC_REMOVE,
            #         Kind.STRUCT: GenericChange.STRUCT_REMOVE,
            #     }[kind]
            #     result.append((btf1.short_version, btf2.short_version, [c]))
            #     continue
            # if t1 is None and t2 is None:
            #     continue
            changes = get_diff_fn(kind)(t1, t2)
            if changes:
                result.append((btf1.short_version, btf2.short_version, changes))
        return result

    def get_versions(self, kind, name):
        result = []
        for btf in self.btfs:
            t = btf.get(kind, name)
            if t is not None:
                result.append(btf.short_version)
        return result
