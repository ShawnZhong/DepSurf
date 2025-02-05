from pathlib import Path

from elftools.elf.elffile import ELFFile

from depsurf.utils import manage_result_path


def get_comment(vmlinux_path: Path) -> str:
    with open(vmlinux_path, "rb") as f:
        elf = ELFFile(f)
        section = elf.get_section_by_name(".comment")
        if section is None:
            return ""
        return section.data().decode().replace("\0", "\n")


@manage_result_path
def dump_comment(vmlinux_path: Path, result_path: Path):
    with open(result_path, "w") as f:
        f.write(get_comment(vmlinux_path))
