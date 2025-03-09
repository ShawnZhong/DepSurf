import logging
import subprocess
import sys

from .color import TermColor


def system(cmd, linux=False):
    if linux:
        if sys.platform == "darwin":
            cmd = f"orbctl run {cmd}"
        else:
            raise RuntimeError("Running linux command on non-Linux platform")

    logging.info(f'Running command: "{TermColor.OKGREEN}{cmd}{TermColor.ENDC}"')
    subprocess.run(cmd, shell=True, check=True, executable="/bin/bash")


__all__ = ["system"]
