from dataclasses import dataclass
from pathlib import Path

from depsurf.paths import DATA_PATH


@dataclass(order=True, frozen=True)
class BuildVersion:
    version_tuple: tuple[int, int, int]
    revision: int
    flavor: str
    arch: str

    @classmethod
    def from_path(cls, path: Path | str):
        return cls.from_str(Path(path).name)

    @classmethod
    def from_str(cls, name: str):
        name = (
            name.removeprefix("linux-image-")
            .removeprefix("unsigned-")
            .removesuffix(".deb")
            .removesuffix(".ddeb")
            .replace("_", "-")
        )

        version, revision, flavor, *others, arch = name.split("-")
        return cls(
            version_tuple=cls.version_to_tuple(version),
            revision=int(revision),
            flavor=flavor,
            arch=arch,
        )

    @staticmethod
    def iter(
        flavor: str = None,
        arch: str = None,
        version: str | tuple = None,
    ) -> list["BuildVersion"]:
        if isinstance(version, str):
            version_tuple = BuildVersion.version_to_tuple(version)
        else:
            version_tuple = version

        results = []
        for deb_path in (DATA_PATH / "deb").iterdir():
            bv = BuildVersion.from_path(deb_path)
            if flavor is not None and bv.flavor != flavor:
                continue
            if arch is not None and bv.arch != arch:
                continue
            if version_tuple is not None and bv.version_tuple != version_tuple:
                continue
            results.append(bv)

        return sorted(results)

    @staticmethod
    def version_to_str(version_tuple: tuple) -> str:
        return ".".join(map(str, version_tuple))

    @staticmethod
    def version_to_tuple(version: str) -> tuple:
        return tuple(map(int, version.split(".")))

    @property
    def version(self):
        return self.version_to_str(self.version_tuple)

    @property
    def short_version(self):
        assert self.version_tuple[-1] == 0
        return self.version_to_str(self.version_tuple[:-1])

    @property
    def name(self):
        return f"{self.version}-{self.revision}-{self.flavor}-{self.arch}"

    @property
    def deb_path(self):
        return DATA_PATH / "deb" / f"{self.name}.deb"

    @property
    def vmlinux_deb_path(self):
        return (
            f"./usr/lib/debug/boot/vmlinux-{self.version}-{self.revision}-{self.flavor}"
        )

    @property
    def vmlinux_path(self):
        return DATA_PATH / "vmlinux" / self.name

    @property
    def btf_path(self):
        return DATA_PATH / "btf" / f"{self.name}"

    @property
    def btf_json_path(self):
        return DATA_PATH / "btf_json" / f"{self.name}.json"

    @property
    def btf_header_path(self):
        return DATA_PATH / "btf_header" / f"{self.name}.h"

    @property
    def btf_txt_path(self):
        return DATA_PATH / "btf_txt" / f"{self.name}.txt"

    @property
    def btf_normalized_path(self):
        return DATA_PATH / "btf_norm" / f"{self.name}.pkl"

    @property
    def symtab_path(self):
        return DATA_PATH / "symtab" / f"{self.name}.pkl"

    def __str__(self):
        return self.name

    def get_img(self):
        from depsurf.linux import LinuxImage

        return LinuxImage(self)

    # @property
    # def vmlinuz_deb_path(self):
    #     return f"./boot/vmlinuz-{self.version_str}-{self.revision}-{self.flavor}"

    # @property
    # def vmlinuz_path(self):
    #     return DATA_PATH / "vmlinuz" / self.name
