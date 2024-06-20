from depsurf.btf import dump_btf_header, dump_btf_json, dump_btf_txt, normalize_btf
from depsurf.funcs import dump_dwarf_funcs
from depsurf.linux import (
    dump_symtab,
    dump_tracepoints,
    extract_btf,
    extract_deb,
)
from depsurf.version import Version
from depsurf.linux_image import LinuxImage


def prep(v: Version, overwrite: bool = False):
    LinuxImage.disable_cache()

    extract_deb(
        deb_path=v.deb_path,
        file_path=v.vmlinux_abs_path,
        result_path=v.vmlinux_path,
        overwrite=overwrite,
    )
    if v.buildinfo_path.exists():
        extract_deb(
            deb_path=v.buildinfo_path,
            file_path=v.config_abs_path,
            result_path=v.config_path,
            overwrite=False,
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
    dump_dwarf_funcs(
        v.vmlinux_path,
        result_path=v.dwarf_funcs_path,
        overwrite=overwrite,
    )
