from pathlib import Path


def get_linux_version_tuple(name):
    """5.13.0-52-generic -> (5, 13, 0)"""
    return tuple(map(int, name.split("-")[0].split(".")))


def get_linux_version_short(name):
    """5.13.0-52-generic -> 5.13"""
    t = get_linux_version_tuple(name)
    assert t[2] == 0
    return f"{t[0]}.{t[1]}"


def get_sorted_linux_paths(paths):
    return sorted(paths, key=lambda p: get_linux_version_tuple(p.stem))


def get_all_x86_paths(ext=".pkl"):
    paths = []
    dirs = sorted(Path("data").glob("*-x86"))
    for d in dirs:
        p = get_sorted_linux_paths(d.glob(f"*{ext}"))
        if d == dirs[-1]:
            paths.extend(p)
        else:
            paths.extend(p[:-1])
    return paths
