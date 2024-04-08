from dataclasses import dataclass

from depsurf.paths import DATA_PATH


def get_linux_version_tuple(name):
    """5.13.0-52-generic -> (5, 13, 0)"""
    return tuple(map(int, name.split("-")[0].split(".")))


def get_linux_version_short(name):
    """5.13.0-52-generic -> 5.13"""
    t = get_linux_version_tuple(name)
    assert t[2] == 0
    return f"{t[0]}.{t[1]}"


@dataclass
class BuildVersion:
    version: tuple[int, int, int]
    revision: int
    flavor: str
    arch: str

    @classmethod
    def from_path(cls, path):
        name = path.stem
        name = name.removeprefix("linux-image-").removeprefix("unsigned-")
        version, revision, flavor, others = name.split("-", 3)

        return cls(
            version=tuple(map(int, version.split("."))),
            revision=int(revision),
            flavor=flavor,
            arch=others.rsplit("_")[-1],
        )

    @property
    def version_str(self):
        return ".".join(map(str, self.version))

    @property
    def name(self):
        return f"{self.version_str}-{self.revision}-{self.flavor}"

    @property
    def full_name(self):
        return f"{self.name}-{self.arch}"

    @property
    def compressed_vmlinux_path(self):
        return f"./usr/lib/debug/boot/vmlinux-{self.name}"

    @property
    def compressed_vmlinuz_path(self):
        return f"./boot/vmlinuz-{self.name}"

    @property
    def vmlinux_path(self):
        return DATA_PATH / "vmlinux" / self.full_name

    @property
    def vmlinuz_path(self):
        return DATA_PATH / "vmlinuz" / self.full_name

    @property
    def btf_path(self):
        return DATA_PATH / "btf" / f"{self.full_name}.btf"
