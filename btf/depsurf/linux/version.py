from dataclasses import dataclass
from pathlib import Path

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
    def from_path(cls, path: Path):
        name = (
            path.name.removeprefix("linux-image-")
            .removeprefix("unsigned-")
            .removesuffix(".deb")
            .removesuffix(".ddeb")
            .replace("_", "-")
        )
        version, revision, flavor, *others, arch = name.split("-")

        return cls(
            version=tuple(map(int, version.split("."))),
            revision=int(revision),
            flavor=flavor,
            arch=arch,
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
    def vmlinux_deb_path(self):
        return f"./usr/lib/debug/boot/vmlinux-{self.name}"

    @property
    def vmlinuz_deb_path(self):
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

    @property
    def btf_json_path(self):
        return self.btf_path.with_suffix(".json")

    @property
    def btf_header_path(self):
        return self.btf_path.with_suffix(".h")

    @property
    def btf_txt_path(self):
        return self.btf_path.with_suffix(".txt")

    @property
    def btf_normalized_path(self):
        return self.btf_path.with_suffix(".pkl")
