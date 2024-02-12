from enum import Enum

class Arch(Enum):
    X86_64 = "x86_64"
    ARM64 = "arm64"


def get_arch():
    import platform

    arch = platform.machine()
    if arch == "x86_64":
        return Arch.X86_64
    elif arch == "arm64" or arch == "aarch64":
        return Arch.ARM64

    raise NotImplementedError(f"Unsupported architecture {arch}")
