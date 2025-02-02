#!/usr/bin/env python3

import os
from pathlib import Path

from utils.arch import Arch, get_arch
from utils.system import system

VM_DATA_PATH = Path("data") / "vm"
KEY_PATH = VM_DATA_PATH / "id_rsa"
TMP_PATH = VM_DATA_PATH / "tmp"
DISK_IMG_PATH = TMP_PATH / "cloudimg.img"
SEED_IMG_PATH = TMP_PATH / "cloud-init-config.iso"


def download(
    url,
    data_path=TMP_PATH,
):
    path = data_path / Path(url).name

    if path.exists():
        print(f"{path} already exists, skipping download")
    else:
        import urllib.request

        print(f"Downloading {url} to {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)

    return path


def get_disk_img_url(
    minimal=False,
    version="20.04",
):
    arch = {
        Arch.X86_64: "amd64",
        Arch.ARM64: "arm64",
    }[get_arch()]

    if minimal:
        return f"https://cloud-images.ubuntu.com/minimal/releases/{version}/release/ubuntu-{version}-minimal-cloudimg-{arch}.img"
    else:
        return f"https://cloud-images.ubuntu.com/releases/{version}/release/ubuntu-{version}-server-cloudimg-{arch}.img"


def prep_disk_img(
    raw_img_path,
    img_path=DISK_IMG_PATH,
    size_gb=64,
):
    if not img_path.exists():
        print(f"Copying {raw_img_path} to {img_path}")
        system(f"cp {raw_img_path} {img_path}")

        print(f"Resizing {img_path} to {size_gb}G")
        system(f"qemu-img resize {img_path} +{size_gb}G")
    else:
        print(f"Disk image {img_path} already exists")

    return img_path


def get_pub_key_local(key_path=KEY_PATH):
    if not key_path.exists():
        print(f"Creating {key_path}")
        system(f"ssh-keygen -q -t rsa -N '' -f {key_path} <<<y >/dev/null 2>&1")

    public_key_path = key_path.with_suffix(".pub")
    return public_key_path.read_text().strip().split("\n")


def get_pub_key_gh(username):
    import json

    import requests

    url = f"https://api.github.com/users/{username}/keys"
    resp = requests.get(url)

    if resp.status_code != 200:
        print(f"Failed to get public key from GitHub: {resp.status_code}")
        return []

    return [f"{k['key']} {username}@github/{k['id']}" for k in json.loads(resp.text)]


def prep_user_data(
    public_keys,
    path=TMP_PATH / "user-data",
):
    import yaml

    if path.exists():
        print(f"{path} already exists, skipping creation")
        return path

    print(f"Creating {path}")

    password = os.urandom(4).hex()
    with open(path, "w") as f:
        f.write("#cloud-config\n")
        data = {
            "ssh_authorized_keys": public_keys,
            "ssh_pwauth": True,
            "password": password,
            "chpasswd": {"expire": False},
        }
        yaml.dump(data, f)

    return path


def prep_meta_data(
    path=TMP_PATH / "meta-data",
):
    if path.exists():
        print(f"{path} already exists, skipping creation")
        return path

    print(f"Creating {path}")
    with open(path, "w") as f:
        f.write("{'instance-id': 'iid-local01'}")
        return path


def prep_seed_img(
    user_data,
    meta_data,
    seed_path=SEED_IMG_PATH,
):
    if seed_path.exists():
        print(f"{seed_path} already exists, skipping creation")
        return seed_path

    print(f"Creating {seed_path}")
    system(
        f"mkisofs -output {seed_path} "
        f"-volid cidata -joliet -rock {user_data} {meta_data}"
    )

    return seed_path


if __name__ == "__main__":
    img_url = get_disk_img_url()
    raw_img_path = download(img_url)
    prep_disk_img(raw_img_path)

    public_keys = get_pub_key_local() + get_pub_key_gh("ShawnZhong")
    user_data = prep_user_data(public_keys)
    meta_data = prep_meta_data()
    prep_seed_img(user_data, meta_data)
