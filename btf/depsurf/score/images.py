from typing import List, Tuple

from depsurf.diff import DiffChanges, get_diff_fn
from depsurf.btf import Kind, BTF
from depsurf.linux import LinuxImage
from depsurf.cause import GenericCause


class KernelImages:
    def __init__(self, imgs: List[LinuxImage]):
        self.imgs = imgs

    @property
    def all_versions(self):
        return [img.version.short_version for img in self.imgs]

    def __len__(self):
        return len(self.imgs)

    def get_changes(self, kind, name) -> List[Tuple[str, str, DiffChanges]]:
        result = []
        for img1, img2 in zip(self.imgs, self.imgs[1:]):
            t1 = img1.btf.get(kind, name)
            t2 = img2.btf.get(kind, name)
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
                result.append(
                    (img1.version.short_version, img2.version.short_version, changes)
                )
        return result

    def get_versions(self, kind, name):
        result = []
        for img in self.imgs:
            t = img.btf.get(kind, name)
            if t is not None:
                result.append(img.version.short_version)
        return result
