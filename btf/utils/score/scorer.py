class Scorer:
    def __init__(self, paths):
        from ..btf import BTF

        self.btfs = [BTF(p) for p in paths]

    @property
    def all_versions(self):
        return [btf.short_version for btf in self.btfs]

    @property
    def num_all_versions(self):
        return len(self.all_versions)

    def get_changes(self, kind, name):
        from ..diff import get_diff_fn, GenericChange

        result = []
        for btf1, btf2 in zip(self.btfs, self.btfs[1:]):
            t1 = btf1.get(kind, name)
            t2 = btf2.get(kind, name)
            if t1 is None and t2 is not None:
                result.append(
                    (btf1.short_version, btf2.short_version, [GenericChange.ADD])
                )
                continue
            if t1 is not None and t2 is None:
                result.append(
                    (btf1.short_version, btf2.short_version, [GenericChange.REMOVE])
                )
                continue
            if t1 is None and t2 is None:
                continue
            diff_fn = get_diff_fn(kind)
            reasons = diff_fn(t1, t2).reasons()
            if reasons:
                result.append((btf1.short_version, btf2.short_version, reasons))
        return result

    def get_versions(self, kind, name):
        result = []
        for btf in self.btfs:
            t = btf.get(kind, name)
            if t is not None:
                result.append(btf.short_version)
        return result
