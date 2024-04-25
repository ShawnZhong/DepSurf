from depsurf.linux import TracepointInfo


def diff_dict(old, new):
    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    common = {k: (old[k], new[k]) for k in old.keys() if k in new}
    return added, removed, common


def compare_eq(t1, t2):
    if isinstance(t1, TracepointInfo) and isinstance(t2, TracepointInfo):
        return compare_eq(t1.struct, t2.struct) and compare_eq(t1.func, t2.func)

    if t1 == t2:
        return True

    if "name" in t1:
        t1 = t1.copy()
        del t1["name"]
    if "name" in t2:
        t2 = t2.copy()
        del t2["name"]
    return t1 == t2
