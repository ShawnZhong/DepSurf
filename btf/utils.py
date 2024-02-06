from enum import Enum

class TermColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def system(cmd):
    import subprocess

    print(f'Running command: "{TermColor.OKGREEN}{cmd}{TermColor.ENDC}"')
    subprocess.run(cmd, shell=True, check=True, executable="/bin/bash")





