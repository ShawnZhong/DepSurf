from functools import cached_property
from typing import List
from pathlib import Path

from elftools.elf.elffile import ELFFile

from depsurf.btf import BTF, dump_btf_json, dump_btf_txt, get_bpftool_path
from depsurf.dep import Dep, DepKind
from depsurf.utils import check_result_path, system


@check_result_path
def gen_min_btf(obj_file, result_path, debug=False):
    debug_arg = "-d" if debug else ""
    system(
        f"{get_bpftool_path()} {debug_arg} gen min_core_btf {obj_file} {result_path} {obj_file}"
    )


DUMMY_HOOK_MAPPING = {
    # Used by fsdist and fsslower
    # Note that only ext4 is built in the kernel by default
    # Ref: https://github.com/iovisor/bcc/blob/fef9003e2e2f29c893543d49b762dd413a352f05/libbpf-tools/fsdist.c#L42-L81
    "dummy_file_read": [
        # "btrfs_file_read_iter",
        "ext4_file_read_iter",
        # "nfs_file_read",
        # "xfs_file_read_iter",
        # "f2fs_file_read_iter",
    ],
    "dummy_file_write": [
        # "btrfs_file_write_iter",
        "ext4_file_write_iter",
        # "nfs_file_write",
        # "xfs_file_write_iter",
        # "f2fs_file_write_iter",
    ],
    "dummy_file_open": [
        # "btrfs_file_open",
        "ext4_file_open",
        # "nfs_file_open",
        # "xfs_file_open",
        # "f2fs_file_open",
    ],
    "dummy_file_sync": [
        # "btrfs_sync_file",
        "ext4_sync_file",
        # "nfs_file_fsync",
        # "xfs_file_fsync",
        # "f2fs_sync_file",
    ],
    "dummy_getattr": [
        "ext4_file_getattr",
        # "nfs_getattr",
        # "f2fs_getattr",
    ],
    # Used by ksnoop
    "foo": [],
    # Used by funclatency
    "dummy_fentry": [],
    "dummy_fexit": [],
    "dummy_kprobe": [],
    "dummy_kretprobe": [],
    # Used by readahead
    # https://github.com/iovisor/bcc/blob/1d8daaa395f066b328a56a36fbd40a0de3a7b3c1/libbpf-tools/readahead.c#L79
    "do_page_cache_ra": [
        "do_page_cache_ra",
        "__do_page_cache_readahead",
    ],
}


class BPFObject:
    def __init__(self, path: Path):
        self.path = path
        self.file = open(path, "rb")
        self.elffile = ELFFile(self.file)

    def __del__(self):
        self.file.close()

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
    def deps_hook(self) -> List[Dep]:

        results = []
        for hook_name in self.hook_names:
            kind = DepKind.from_hook_name(hook_name)
            if "/" in hook_name:
                name = hook_name.rsplit("/", 1)[-1]
            else:
                name = ""

            for prefix in ["sys_enter_", "sys_exit_"]:
                if name.startswith(prefix):
                    assert kind == DepKind.SYSCALL
                    name = name[len(prefix) :]

            if name in DUMMY_HOOK_MAPPING:
                for dep_name in DUMMY_HOOK_MAPPING[name]:
                    results.append(Dep(kind, dep_name))
            else:
                results.append(Dep(kind, name))

        return sorted(set(results))

    @property
    def deps_struct(self) -> list[Dep]:
        gen_min_btf(
            self.path,
            result_path=self.btf_file,
            overwrite=False,
            slient=True,
        )
        dump_btf_json(
            self.btf_file,
            result_path=self.btf_json_file,
            overwrite=False,
            slient=True,
        )
        dump_btf_txt(
            self.btf_file,
            result_path=self.btf_txt_file,
            overwrite=False,
            slient=True,
        )
        btf = BTF.from_raw_json(self.btf_json_file)

        results = []
        for name, struct in btf.structs.items():
            name = name.split("___")[0]
            if name == "user_pt_regs":
                continue
            results.append(DepKind.STRUCT(name))
            for member in struct["members"]:
                results.append(DepKind.FIELD(f"{name}::{member['name']}"))

        return sorted(set(results))

    @cached_property
    def deps(self) -> list[Dep]:
        return sorted(self.deps_hook + self.deps_struct)

    # @property
    # def deps_struct_field(self):
    #     from .relo import BTFReloInfo, BTFExtSection, BTFStrtab, RawBTF

    #     dump_btf_json(self.path, result_path=self.btf_json_file, overwrite=False)
    #     return BTFReloInfo(
    #         BTFExtSection.from_elf(self.elffile).relo_info,
    #         BTFStrtab(self.elffile),
    #         RawBTF.load(self.btf_json_file),
    #     ).get_deps()
