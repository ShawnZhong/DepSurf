def download_package_index(package_url, result_path):
    import urllib.request
    import gzip

    result_path.mkdir(parents=True, exist_ok=True)
    gz_path = result_path / "Packages.gz"

    if not gz_path.exists():
        print(f"Downloading {package_url} to {gz_path}")
        urllib.request.urlretrieve(package_url, gz_path)
    else:
        print(f"Using {gz_path}")

    package_path = gz_path.with_suffix("")
    if not package_path.with_suffix("").exists():
        print(f"Unzipping {gz_path} to {package_path}")
        with gzip.open(gz_path, "rb") as f_in:
            with open(package_path, "wb") as f_out:
                f_out.write(f_in.read())
    else:
        print(f"Using {package_path}")

    return package_path


def parse_package_index(package_path):
    result = {}
    with open(package_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            key, val = line.split(": ", 1)
            if key == "Package":
                package = val
            elif key == "Filename":
                result[package] = val
    return result


def filter_linux_images(package_index):
    import re
    from collections import defaultdict

    result = defaultdict(dict)
    for package, path in package_index.items():
        groups = re.match(r"^linux-image-(\d+\.\d+\.\d+)-(\d+)-generic$", package)
        if groups is None:
            continue

        version, build = groups.groups()
        package = package.removeprefix("linux-image-")
        result[version][int(build)] = package, path

    return [v[max(v.keys())] for v in result.values()]


def download_deb_files(linux_versions, url_prefix, result_path):
    import urllib.request

    result_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, path in linux_versions:
        url = f"{url_prefix}/{path}"
        file_path = result_path / path.split("/")[-1]
        if not file_path.exists():
            print(f"Downloading {url} to {file_path}")
            urllib.request.urlretrieve(url, file_path)
        else:
            print(f"Using {file_path}")

        results[name] = file_path

    return results
