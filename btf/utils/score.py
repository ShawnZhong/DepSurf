def get_structs(obj_file):
    from .btf import Kind
    from .btf_normalize import normalize_btf
    from .bpftool import gen_min_btf, dump_btf

    btf_file = gen_min_btf(obj_file)
    dump_btf(btf_file)
    data = normalize_btf(btf_file)

    if Kind.STRUCT not in data:
        return []

    return [e for e in data[Kind.STRUCT].keys() if e != "user_pt_regs"]


def normalize_hook_name(name):
    for hook_type, prefixes in [
        ("kprobe", ["kprobe/", "kretprobe/", "fentry/", "fexit/"]),
        ("tracepoint", ["tp_btf/", "raw_tp/", "tracepoint/"]),
        ("uprobe", ["uprobe/", "uretprobe/", "uprobe", "uretprobe"]),
        ("usdt", ["usdt"]),
        ("perf_event", ["perf_event"]),
    ]:
        for prefix in prefixes:
            if not name.startswith(prefix):
                continue

            name = name[len(prefix) :]
            if "/" in name:
                assert prefix == "tracepoint/"
                name = name.rsplit("/", 1)[-1]
            return (hook_type, name)

    raise ValueError(f"Unknown hook type: {name}")


def get_hooks(obj_file):
    from elftools.elf.elffile import ELFFile

    with open(obj_file, "rb") as f:
        elf = ELFFile(f)

        hooks = set()
        for section in elf.iter_sections():
            if section.name.startswith("."):
                continue
            if section.name == "license":
                continue
            if section.header.sh_type == "SHT_PROGBITS":
                name = normalize_hook_name(section.name)
                hooks.add(name)
        return hooks


def get_changes(btfs, kind, name):
    from .btf_diff import get_diff_fn, GenericChange

    result = []
    for btf1, btf2 in zip(btfs, btfs[1:]):
        t1 = btf1.get(kind, name)
        t2 = btf2.get(kind, name)
        if t1 is None and t2 is not None:
            result.append((btf1.short_version, btf2.short_version, [GenericChange.ADD]))
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


def get_available_versions(btfs, kind, name):
    result = []
    for btf in btfs:
        t = btf.get(kind, name)
        if t is not None:
            result.append(btf.short_version)

    return result
