from dataclasses import dataclass


def get_linux_version_tuple(name):
    """5.13.0-52-generic -> (5, 13, 0)"""
    return tuple(map(int, name.split("-")[0].split(".")))


def get_linux_version_short(name):
    """5.13.0-52-generic -> 5.13"""
    t = get_linux_version_tuple(name)
    assert t[2] == 0
    return f"{t[0]}.{t[1]}"


@dataclass(frozen=True)
class UbuntuVersion:
    version: str
    arch: str

    @property
    def path(self):
        from ..paths import DATA_PATH

        return DATA_PATH / f"{self.version}-{self.arch}"

    @property
    def version_name(self):
        return {
            "16.04": "xenial",
            "18.04": "bionic",
            "20.04": "focal",
            "22.04": "jammy",
        }[self.version]

    @property
    def url_prefix(self):
        return {
            "x86": "http://security.ubuntu.com/ubuntu",
            "arm64": "http://ports.ubuntu.com/ubuntu-ports",
        }[self.arch]

    @property
    def url(self):
        return f"{self.url_prefix}/dists/{self.version_name}-security/main/binary-{self.arch}/Packages.gz"

    @property
    def index_path(self):
        return self.path / "index"

    @property
    def deb_path(self):
        return self.path / "debs"

    @property
    def vmlinux_path(self):
        return self.path / "vmlinux"

    @property
    def vmlinuz_path(self):
        return self.path / "vmlinuz"

    @property
    def btf_path(self):
        return self.path / "btf"
