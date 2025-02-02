from depsurf.btf import normalize_btf
from depsurf.funcs import dump_func_entries, dump_func_groups
from depsurf.linux import (
    dump_symtab,
    dump_syscalls,
    dump_tracepoints,
    extract_raw_btf,
    extract_deb,
)
from depsurf.linux_image import LinuxImage
from depsurf.utils import dump_raw_btf_header, dump_raw_btf_json, dump_raw_btf_txt
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
    if v.image_deb_path.exists():
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
    extract_raw_btf(
        vmlinux_path=v.vmlinux_path,
        result_path=v.raw_btf_path,
        overwrite=overwrite,
    )
    dump_raw_btf_json(
        raw_btf_path=v.raw_btf_path,
        result_path=v.raw_btf_json_path,
        overwrite=overwrite,
    )
    dump_raw_btf_txt(
        raw_btf_path=v.raw_btf_path,
        result_path=v.raw_btf_txt_path,
        overwrite=overwrite,
    )
    dump_raw_btf_header(
        raw_btf_path=v.raw_btf_path,
        result_path=v.raw_btf_header_path,
        overwrite=overwrite,
    )

    # Dump the normalized BTF, symbol table, tracepoints, functions, and syscalls
    normalize_btf(
        v.raw_btf_json_path,
        result_path=v.btf_path,
        overwrite=overwrite,
    )
    dump_symtab(
        vmlinux_path=v.vmlinux_path,
        result_path=v.symtab_path,
        overwrite=overwrite,
    )
    dump_func_entries(
        v.vmlinux_path,
        result_path=v.func_entries_path,
        overwrite=overwrite,
    )
    dump_func_groups(
        funcs_path=v.func_entries_path,
        symtab_path=v.symtab_path,
        result_path=v.func_groups_path,
        overwrite=overwrite,
    )
    dump_tracepoints(
        img=v.img,
        result_path=v.tracepoints_path,
        overwrite=overwrite,
    )
    dump_syscalls(
        img=v.img,
        result_path=v.syscalls_path,
        overwrite=overwrite,
    )
