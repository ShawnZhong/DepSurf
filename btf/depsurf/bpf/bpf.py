from depsurf.btf import BTF, dump_btf_json, get_bpftool_path, dump_btf_header
from depsurf.deps import DepKind
from depsurf.elf import ObjectFile
from depsurf.utils import check_result_path, system

from .relo import BTFReloInfo, BTFExtSection, BTFStrtab, RawBTF


@check_result_path
def gen_min_btf(obj_file, result_path):
    kernel_btf = "/sys/kernel/btf/vmlinux"
    system(
        f"/Users/szhong/Downloads/bpf-study/bcc/libbpf-tools/bpftool/src/bpftool -d gen min_core_btf {kernel_btf} {result_path} {obj_file}"
    )


class BPFObject(ObjectFile):
    def __init__(self, path):
        super().__init__(path)

    @property
    def name(self):
        return self.path.name.removesuffix(".o").removesuffix(".bpf")

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
    def min_btf_file(self):
        return self.path.with_suffix(".min.btf")

    @property
    def min_btf_json_file(self):
        return self.path.with_suffix(".min.btf.json")

    @property
    def min_btf_header_file(self):
        return self.path.with_suffix(".min.btf.h")

    @property
    def btf_json_file(self):
        return self.path.with_suffix(".btf.json")

    @property
    def deps_struct(self) -> list[tuple[DepKind, str]]:
        gen_min_btf(self.path, result_path=self.min_btf_file, overwrite=True)
        dump_btf_json(
            self.min_btf_file, result_path=self.min_btf_json_file, overwrite=True
        )
        dump_btf_header(
            self.min_btf_file, result_path=self.min_btf_header_file, overwrite=True
        )
        print(self.min_btf_header_file)
        btf = BTF.from_raw_json(self.min_btf_json_file)
        d = sorted(
            [(name, m["name"]) for name, e in btf.structs.items() for m in e["members"]]
        )
        for e in d:
            print(e)

        # for name, e in btf.structs.items():
        #     for m in e["members"]:
        #         print(name, m["name"])
        return [(DepKind.STRUCT, e) for e in btf.structs]

    @property
    def deps(self) -> list[tuple[DepKind, str]]:
        return self.deps_hook + self.deps_struct

    @property
    def deps_struct_field(self):
        dump_btf_json(self.path, result_path=self.btf_json_file, overwrite=False)
        return BTFReloInfo(
            BTFExtSection.from_elf(self.elffile).relo_info,
            BTFStrtab(self.elffile),
            RawBTF.load(self.btf_json_file),
        ).get_deps()
