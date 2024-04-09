from pathlib import Path
import logging

# from depsurf.linux.version import get_linux_version_short, get_linux_version_tuple


class BTF:
    def __init__(self, path):
        import pickle

        self.path = Path(path)
        assert self.path.exists()
        assert self.path.suffix == ".pkl"
        with open(self.path, "rb") as f:
            logging.info(f"Loading {self.path}")
            self.data = pickle.load(f)

    def __repr__(self):
        result = f"File: {self.path}\n"
        result += "Sample:\n"
        for kind, d in self.data.items():
            result += f"\t{kind:10} ({len(d):5}): {list(d.values())[0]}\n"
        return result

    @property
    def short_version(self):
        pass
        # return get_linux_version_short(self.path.stem)

    @property
    def version(self):
        pass
        # return get_linux_version_tuple(self.path.stem)

    def filter(self, kind, name_filter_fn=None):
        if not name_filter_fn:
            return self.data[kind]
        else:
            return {k: v for k, v in self.data[kind].items() if name_filter_fn(k)}

    def get(self, arg1, arg2=None):
        if isinstance(arg1, tuple):
            assert arg2 is None
            kind, name = arg1
        else:
            kind = arg1
            name = arg2

        if name is None:
            return self.data[kind]
        else:
            return self.data[kind].get(name, None)
