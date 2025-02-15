import logging
import subprocess

from .color import TermColor


def system(cmd):
    logging.info(f'Running command: "{TermColor.OKGREEN}{cmd}{TermColor.ENDC}"')
    subprocess.run(cmd, shell=True, check=True, executable="/bin/bash")


__all__ = ["system"]
