def get_linux_version_tuple(name):
    """5.13.0-52-generic -> (5, 13, 0)"""
    return tuple(map(int, name.split("-")[0].split(".")))


def get_linux_version_short(name):
    """5.13.0-52-generic -> 5.13"""
    t = get_linux_version_tuple(name)
    assert t[2] == 0
    return f"{t[0]}.{t[1]}"
