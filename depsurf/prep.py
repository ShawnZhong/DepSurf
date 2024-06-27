from depsurf.btf import normalize_btf
from depsurf.funcs import dump_funcs
from depsurf.linux import (
    dump_symtab,
    dump_syscalls,
    dump_tracepoints,
    extract_btf,
    extract_deb,
)
from depsurf.linux_image import LinuxImage
from depsurf.utils import dump_btf_header, dump_btf_json, dump_btf_txt
from depsurf.version import Version


def prep(v: Version, overwrite: bool = False):
    LinuxImage.disable_cache()

    # Extract the Linux image with debug info
    extract_deb(
        deb_path=v.dbgsym_deb_path,
        file_path=f"/usr/lib/debug/boot/vmlinux-{v.short_name}",
        result_path=v.vmlinux_path,
        overwrite=overwrite,
    )

    # Extract the boot image
    extract_deb(
        deb_path=v.image_deb_path,
        file_path=(
            f"/boot/vmlinux-{v.short_name}"
            if v.arch == "ppc64el"
            else f"/boot/vmlinuz-{v.short_name}"
        ),
        result_path=v.vmlinuz_path,
        overwrite=overwrite,
    )

    # Extract the config file
    if v.buildinfo_path.exists():  # from buildinfo
        extract_deb(
            deb_path=v.buildinfo_path,
            file_path=f"/usr/lib/linux/{v.short_name}/config",
            result_path=v.config_path,
            overwrite=overwrite,
        )
    elif v.modules_deb_path.exists():  # from modules
        extract_deb(
            deb_path=v.modules_deb_path,
            file_path=f"/boot/config-{v.short_name}",
            result_path=v.config_path,
            overwrite=overwrite,
        )
    else:  # from image
        extract_deb(
            deb_path=v.image_deb_path,
            file_path=f"/boot/config-{v.short_name}",
            result_path=v.config_path,
            overwrite=overwrite,
        )

    # Extract the raw BTF
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

    # Dump the normalized BTF, symbol table, tracepoints, functions, and syscalls
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
    dump_funcs(
        v.vmlinux_path,
        result_path=v.funcs_path,
        overwrite=overwrite,
    )
    dump_syscalls(
        img=v.img,
        result_path=v.syscalls_path,
        overwrite=overwrite,
    )
