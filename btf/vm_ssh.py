#!/usr/bin/env python3

from utils import system
from vm_prep import KEY_PATH
import argparse


def ssh(port, key_path):
    system(
        f'ssh -p {port} -i {key_path} -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking=no" ubuntu@localhost'
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("idx", type=int, default=0, nargs="?")
    args = parser.parse_args()
    idx = args.idx

    ssh(2222 + idx, KEY_PATH)
