#!/bin/env python3

import os
import shutil

deps = [
    ("cmake", "cmake"),
    ("clang++", "clang"),
    ("pkg-config", "pkg-config"),
    ("/usr/include/gelf.h", "libelf-dev"),
]


def install_deps():
    pkgs = [pkg for name, pkg in deps if shutil.which(name, mode=os.F_OK) is None]
    if pkgs:
        print(f"Installing {pkgs}")
        os.system(f"sudo apt update && sudo apt install {' '.join(pkgs)}")
    else:
        print("All dependencies already installed")


if __name__ == "__main__":
    install_deps()
