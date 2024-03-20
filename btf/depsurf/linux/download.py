from .utils import download, unzip_gz


def download_package_index(package_url, result_path, overwrite=False):
    result_path.mkdir(parents=True, exist_ok=True)

    # download
    gz_path = result_path / "Packages.gz"
    download(package_url, gz_path, overwrite=overwrite)

    # unzip
    package_path = gz_path.with_suffix("")
    unzip_gz(gz_path, package_path, overwrite=overwrite)

    return package_path


def parse_package_index(package_path):
    result = {}
    with open(package_path) as f:
        for line in f:
            if ": " not in line:
                continue

            line = line.strip()

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
        groups = re.match(
            r"^linux-image-(\d+\.\d+\.\d+)-(\d+)-generic(?:-.+)?$", package
        )
        if groups is None:
            continue

        version, build = groups.groups()
        package = package.removeprefix("linux-image-")
        result[version][int(build)] = package, path

    return [v[max(v.keys())] for v in result.values()]


def download_deb_files(linux_versions, url_prefix, result_path, overwrite=False):
    result_path.mkdir(parents=True, exist_ok=True)

    results = {}
    for name, path in linux_versions:
        url = f"{url_prefix}/{path}"
        file_path = result_path / path.split("/")[-1]
        download(url, file_path, overwrite=overwrite)
        results[name] = file_path

    return results
