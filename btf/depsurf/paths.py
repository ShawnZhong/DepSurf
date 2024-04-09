from pathlib import Path

PROJ_PATH = Path(__file__).parent.parent

DATA_PATH = PROJ_PATH / "data"
assert DATA_PATH.exists(), f"{DATA_PATH} does not exist"

OUTPUT_PATH = PROJ_PATH / "output"
assert OUTPUT_PATH.exists(), f"{OUTPUT_PATH} does not exist"

BCC_PATH = PROJ_PATH.parent / "bcc"
assert BCC_PATH.exists(), f"{BCC_PATH} does not exist"

BCC_OUTPUT_PATH = BCC_PATH / "libbpf-tools" / ".output"


def get_sorted_linux_paths(paths):
    from .linux.version import get_linux_version_tuple

    return sorted(paths, key=lambda p: get_linux_version_tuple(p.stem))


def get_all_x86_paths(ext=".pkl"):
    paths = []
    dirs = sorted(DATA_PATH.glob("*-x86"))
    for d in dirs:
        p = get_sorted_linux_paths(d.glob(f"**/*{ext}"))
        if d == dirs[-1]:
            paths.extend(p)
        else:
            paths.extend(p[:-1])
    return paths
