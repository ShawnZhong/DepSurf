from typing import Dict, Tuple


def diff_nop(old, new):
    return []


def diff_dict(
    old: Dict, new: Dict
) -> Tuple[Dict[str, Dict], Dict[str, Dict], Dict[str, Tuple[Dict, Dict]]]:
    added = {k: v for k, v in new.items() if k not in old}
    removed = {k: v for k, v in old.items() if k not in new}
    common = {k: (old[k], new[k]) for k in old.keys() if k in new}
    return added, removed, common
