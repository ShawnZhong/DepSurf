import logging
import re
from pathlib import Path
from typing import Dict, Optional


def get_configs(path: Path) -> Dict[str, Optional[str]]:
    with open(path, "r") as f:
        lines = f.readlines()

    configs = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue

        groups = re.match(r"# CONFIG_(\w+) is not set", line)
        if groups:
            configs[groups[1]] = None
            continue

        groups = re.match(r"CONFIG_(\w+)=(.*)", line)
        if groups:
            configs[groups[1]] = groups[2]
            continue

        if line[0] == "#":
            continue

        logging.warning(f"Unrecognized line in {path}: {line}")

    return configs
