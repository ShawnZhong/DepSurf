#!/usr/bin/env python3

import argparse
import os

from prep import DISK_IMG_PATH, SEED_IMG_PATH, VM_DATA_PATH
from utils.arch import Arch, get_arch
from utils.system import system


def get_qemu_path():
    return {
        Arch.X86_64: "qemu-system-x86_64",
        Arch.ARM64: "qemu-system-aarch64",
    }[get_arch()]


def run_qemu(img_path, core_count, port, debug=False):
    if os.system(f"nc -z localhost {port}") == 0:
        print(f"Port {port} is already in use. Please close the process and try again.")
        exit(1)

    accel = "kvm" if get_arch() == Arch.X86_64 else "hvf"

    cmd = (
        f"sudo {get_qemu_path()} "
        f"-smp {core_count} "  # use all host cores
        f"-cpu max "  # use host CPU
        f"-accel {accel} "  # try to use HVF acceleration
        f"-m 16G "
        f"-nographic "
        f"-device virtio-net-pci,netdev=net0 "  # virtio network device
        f"-netdev user,id=net0,hostfwd=tcp::{port}-:22 "  # ssh port forwarding
        f"-drive if=virtio,format=qcow2,file={img_path} "
        f"-cdrom {SEED_IMG_PATH} "
        f"-virtfs local,path=..,security_model=passthrough,mount_tag=host0"
    )

    if get_arch() == Arch.ARM64:
        cmd += f"-machine virt "  # use virt machine
        cmd += f"-bios support/AAVMF_CODE.fd "  # specify UEFI image

    if debug:
        cmd += "-s "  # shorthand for -gdb tcp::1234
        cmd += "-S "  # freezes CPU at startup (use 'c' in gdb to continue)

    system(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("index", type=int, default=0, nargs="?")
    args = parser.parse_args()
    idx = args.index

    if idx == 0:
        img_path = DISK_IMG_PATH
    else:
        img_path = VM_DATA_PATH / f"cloudimg-{idx}.img"
        if not img_path.exists():
            system(f"cp {DISK_IMG_PATH} {img_path}")
        else:
            print(f"Using existing image {img_path}")

    core_count = os.cpu_count() // 4
    run_qemu(
        img_path=img_path,
        core_count=core_count,
        port=2222 + idx,
    )


if __name__ == "__main__":
    main()
