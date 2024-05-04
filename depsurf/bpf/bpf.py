from depsurf.btf import BTF, dump_btf_json, dump_btf_txt, get_bpftool_path
from depsurf.deps import DepKind
from depsurf.elf import ObjectFile
from depsurf.utils import check_result_path, system
from depsurf.version import Version

from pathlib import Path

from functools import cached_property


@check_result_path
def gen_min_btf(obj_file, result_path, debug=False):
    debug_arg = "-d" if debug else ""
    system(
        f"{get_bpftool_path()} {debug_arg} gen min_core_btf {obj_file} {result_path} {obj_file}"
    )


class BPFObject(ObjectFile):
    def __init__(self, path):
        super().__init__(path)

    @property
    def name(self):
        return self.path.name.removesuffix(".o").removesuffix(".bpf")

    @property
    def btf_file(self):
        return self.path.with_suffix(".min.btf")

    @property
    def btf_json_file(self):
        return self.path.with_suffix(".min.btf.json")

    @property
    def btf_txt_file(self):
        return self.path.with_suffix(".min.btf.txt")

    @property
    def hook_names(self):
        return [
            section.name
            for section in self.elffile.iter_sections()
            if not section.name.startswith(".")
            and section.name != "license"
            and section.header.sh_type == "SHT_PROGBITS"
        ]

    @property
    def deps_hook(self) -> list[tuple[DepKind, str]]:
        return sorted(
            set(
                (
                    DepKind.from_hook_name(hook_name),
                    "" if "/" not in hook_name else hook_name.rsplit("/", 1)[-1],
                )
                for hook_name in self.hook_names
            )
        )

    @property
    def deps_struct(self) -> list[tuple[DepKind, str]]:
        gen_min_btf(self.path, result_path=self.btf_file, overwrite=False)
        dump_btf_json(self.btf_file, result_path=self.btf_json_file, overwrite=False)
        dump_btf_txt(self.btf_file, result_path=self.btf_txt_file, overwrite=False)
        btf = BTF.from_raw_json(self.btf_json_file)

        return sorted(
            set(
                (DepKind.STRUCT_FIELD, f'{name.split("___")[0]}::{member["name"]}')
                for name, struct in btf.structs.items()
                for member in struct["members"]
            )
        )

    @cached_property
    def deps(self) -> list[tuple[DepKind, str]]:
        return self.deps_hook + self.deps_struct

    # @property
    # def btf_json_file(self):
    #     return self.path.with_suffix(".btf.json")

    # @property
    # def deps_struct_field(self):
    #     from .relo import BTFReloInfo, BTFExtSection, BTFStrtab, RawBTF

    #     dump_btf_json(self.path, result_path=self.btf_json_file, overwrite=False)
    #     return BTFReloInfo(
    #         BTFExtSection.from_elf(self.elffile).relo_info,
    #         BTFStrtab(self.elffile),
    #         RawBTF.load(self.btf_json_file),
    #     ).get_deps()
