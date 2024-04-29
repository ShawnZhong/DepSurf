import sys
import logging
from pathlib import Path


class FileLogger:
    def __init__(self, path, print=False):
        if path is None:
            self.log = None
        elif isinstance(path, (str, Path)):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.log = open(path, "w")

        self.print = print
        self.stdout = sys.stdout

        logging.debug(f"Logging to {path}")

    def write(self, message):
        if self.log:
            self.log.write(message)
        if self.print:
            self.stdout.write(message)

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.stdout
        if self.log:
            self.log.close()
