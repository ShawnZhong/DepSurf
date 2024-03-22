import sys
import logging
from pathlib import Path


class FileLogger:
    def __init__(self, path, print=False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.print = print
        self.stdout = sys.stdout
        self.log = open(path, "w")

        logging.debug(f"Logging to {path}")

    def write(self, message):
        self.log.write(message)
        if self.print:
            self.stdout.write(message)

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.stdout
        self.log.close()
