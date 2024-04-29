from depsurf.btf import BTF, dump_btf_json, get_bpftool_path
from depsurf.deps import DepKind
from depsurf.elf import ObjectFile
from depsurf.utils import check_result_path, system


@check_result_path
def gen_min_btf(obj_file, result_path):
    kernel_btf = "/sys/kernel/btf/vmlinux"
    system(
        f"{get_bpftool_path()} gen min_core_btf {kernel_btf} {result_path} {obj_file}"
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
    def deps_struct(self) -> list[tuple[DepKind, str]]:
        btf_file = self.path.with_suffix(".min.btf")
        gen_min_btf(self.path, result_path=btf_file, overwrite=False)

        btf_json_file = btf_file.with_suffix(".json")
        dump_btf_json(btf_file, result_path=btf_json_file, overwrite=False)

        btf = BTF.from_raw_json(btf_json_file)
        return [(DepKind.STRUCT, e) for e in btf.structs]

    @property
    def deps(self) -> list[tuple[DepKind, str]]:
        return self.deps_hook + self.deps_struct
