def get_linux_tools_path():
    parent = Path("/usr/lib/linux-tools")
    versions = [x for x in parent.iterdir() if x.is_dir()]
    if len(versions) == 0:
        raise Exception("No linux-tools found")
    versions.sort()
    return parent / versions[-1]


def get_bpftool_path():
    bpftool_path = BPFTOOL_SRC_PATH / "bpftool"
    if bpftool_path.exists():
        return bpftool_path

    path = get_linux_tools_path() / "bpftool"
    if not path.exists():
        raise Exception("bpftool not found")
    return path
