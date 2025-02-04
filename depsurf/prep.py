from depsurf.btf import dump_types, dump_btf_header, dump_btf_json, dump_btf_txt
from depsurf.funcs import dump_func_entries, dump_func_groups
from depsurf.linux import (
    dump_symtab,
    dump_syscalls,
    dump_tracepoints,
    extract_btf,
    extract_deb,
)
from depsurf.linux_image import LinuxImage
from depsurf.version import Version


def prep(v: Version):
    LinuxImage.disable_cache()

    # Extract the Linux image with debug info
    extract_deb(
        deb_path=v.dbgsym_download_path,
        file_path=f"/usr/lib/debug/boot/vmlinux-{v.short_name}",
        result_path=v.vmlinux_path,
    )

    # Extract the boot image
    if v.image_download_path.exists():
        extract_deb(
            deb_path=v.image_download_path,
            file_path=(
                f"/boot/vmlinux-{v.short_name}"
                if v.arch == "ppc64el"
                else f"/boot/vmlinuz-{v.short_name}"
            ),
            result_path=v.vmlinuz_path,
        )

    # Extract the config file
    if v.buildinfo_download_path.exists():  # from buildinfo
        extract_deb(
            deb_path=v.buildinfo_download_path,
            file_path=f"/usr/lib/linux/{v.short_name}/config",
            result_path=v.config_path,
        )
    elif v.modules_download_path.exists():  # from modules
        extract_deb(
            deb_path=v.modules_download_path,
            file_path=f"/boot/config-{v.short_name}",
            result_path=v.config_path,
        )
    else:  # from image
        extract_deb(
            deb_path=v.image_download_path,
            file_path=f"/boot/config-{v.short_name}",
            result_path=v.config_path,
        )

    # Extract BTF
    extract_btf(
        vmlinux_path=v.vmlinux_path,
        result_path=v.btf_path,
    )
    dump_btf_json(
        raw_btf_path=v.btf_path,
        result_path=v.btf_json_path,
    )
    dump_btf_txt(
        raw_btf_path=v.btf_path,
        result_path=v.btf_txt_path,
    )
    dump_btf_header(
        raw_btf_path=v.btf_path,
        result_path=v.btf_header_path,
    )

    # Dump the types, symbol table, tracepoints, functions, and syscalls
    dump_types(
        v.btf_json_path,
        result_path=v.types_path,
    )
    dump_symtab(
        vmlinux_path=v.vmlinux_path,
        result_path=v.symtab_path,
    )
    dump_func_entries(
        v.vmlinux_path,
        result_path=v.func_entries_path,
    )
    dump_func_groups(
        funcs_path=v.func_entries_path,
        symtab_path=v.symtab_path,
        result_path=v.func_groups_path,
    )
    dump_tracepoints(
        img=v.img,
        result_path=v.tracepoints_path,
    )
    dump_syscalls(
        img=v.img,
        result_path=v.syscalls_path,
    )
