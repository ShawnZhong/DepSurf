def get_linux_tools_path():
    from pathlib import Path

    parent = Path("/usr/lib/linux-tools")
    versions = [x for x in parent.iterdir() if x.is_dir()]
    if len(versions) == 0:
        raise Exception("No linux-tools found")
    versions.sort()
    return parent / versions[-1]


def get_bpftool_path():
    path = get_linux_tools_path() / "bpftool"
    if not path.exists():
        raise Exception("bpftool not found")
    return path


BPFTOOL_PATH = get_bpftool_path()


def gen_min_btf(obj_file, overwrite=False):
    from .system import system

    btf_file = obj_file.with_suffix(".btf")
    if btf_file.exists() and not overwrite:
        print(f"{btf_file} already exists")
        return btf_file

    kernel_btf = "/sys/kernel/btf/vmlinux"
    system(f"{BPFTOOL_PATH} gen min_core_btf {kernel_btf} {btf_file} {obj_file}")


def dump_btf(file, overwrite=False):
    from .system import system

    for ext, cmd in [
        (".h", "format c"),
        (".txt", "format raw"),
        (".json", "--json"),
    ]:
        result = file.with_suffix(ext)

        if result.exists() and not overwrite:
            print(f"{result} already exists")
            continue

        system(f"{BPFTOOL_PATH} btf dump file {file} {cmd} > {result}")


if __name__ == "__main__":
    print(BPFTOOL_PATH)
