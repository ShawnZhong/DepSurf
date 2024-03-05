def parse_structs(obj_file):
    from ..btf import Kind, BTF
    from ..normalize import normalize_btf
    from ..bpftool import gen_min_btf, dump_btf

    btf_file = gen_min_btf(obj_file)
    dump_btf(btf_file)
    pkl_path = normalize_btf(btf_file)

    btf = BTF(pkl_path)
    if Kind.STRUCT not in btf.data:
        return []

    return [e for e in btf.data[Kind.STRUCT].keys() if e != "user_pt_regs"]


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


def parse_hooks(obj_file):
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
