#!/usr/bin/env python3

import argparse

from prep import KEY_PATH
from utils.system import system


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
