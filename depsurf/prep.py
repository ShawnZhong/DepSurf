from depsurf.version import Version
from depsurf.btf import (
    dump_btf_json,
    dump_btf_txt,
    dump_btf_header,
    normalize_btf,
)
from depsurf.linux import extract_deb, dump_tracepoints, LinuxImage
from depsurf.elf import dump_symtab, extract_btf
from depsurf.dwarf import dump_funcs


def prep(v: Version, overwrite: bool = False):
    LinuxImage.disable_cache()

    extract_deb(
        deb_path=v.deb_path,
        file_path=v.vmlinux_deb_path,
        result_path=v.vmlinux_path,
        overwrite=overwrite,
    )
    extract_btf(
        vmlinux_path=v.vmlinux_path,
        result_path=v.btf_path,
        overwrite=overwrite,
    )
    dump_btf_json(
        btf_path=v.btf_path,
        result_path=v.btf_json_path,
        overwrite=overwrite,
    )
    dump_btf_txt(
        btf_path=v.btf_path,
        result_path=v.btf_txt_path,
        overwrite=overwrite,
    )
    dump_btf_header(
        btf_path=v.btf_path,
        result_path=v.btf_header_path,
        overwrite=overwrite,
    )
    normalize_btf(
        v.btf_json_path,
        result_path=v.btf_norm_path,
        overwrite=overwrite,
    )
    dump_symtab(
        vmlinux_path=v.vmlinux_path,
        result_path=v.symtab_path,
        overwrite=overwrite,
    )
    dump_tracepoints(
        img=v.img,
        result_path=v.tracepoints_path,
        overwrite=overwrite,
    )


def prep_dwarf(v: Version, overwrite: bool = False):
    dump_funcs(
        v.vmlinux_path,
        result_path=v.funcs_path,
        overwrite=overwrite,
    )
