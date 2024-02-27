import sys


class FileLogger:
    def __init__(self, path):
        # print(f"Logging to {path}")

        self.stdout = sys.stdout
        path.parent.mkdir(parents=True, exist_ok=True)
        self.log = open(path, "w")

    def write(self, message):
        self.log.write(message)

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.stdout
        self.log.close()
