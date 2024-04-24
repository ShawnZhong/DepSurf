def parse_structs(obj_file, overwrite=False):
    from depsurf.btf import Kind, BTF, normalize_btf, gen_min_btf, dump_btf

    btf_file = gen_min_btf(obj_file, overwrite=overwrite)
    btf_json_file = btf_file.with_suffix(".json")
    dump_btf(btf_file, result_paths=[btf_json_file], overwrite=overwrite)

    btf_pkl_path = btf_file.with_suffix(".pkl")
    normalize_btf(
        json_path=btf_json_file, result_path=btf_pkl_path, overwrite=overwrite
    )

    btf = BTF(btf_pkl_path)
    if Kind.STRUCT not in btf.data:
        return []

    return [("struct", e) for e in btf.data[Kind.STRUCT].keys() if e != "user_pt_regs"]


def normalize_hook_name(name):
    for hook_type, prefixes in [
        ("func", ["kprobe/", "kretprobe/", "fentry/", "fexit/"]),
        (
            "syscall",
            ["tracepoint/syscalls/", "tracepoint/syscalls/"],
        ),
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
