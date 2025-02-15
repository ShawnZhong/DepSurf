import logging
from pathlib import Path

from .color import TermColor


def manage_result_path(fn):
    def wrapper(*args, **kwargs):
        fn_name = fn.__name__

        def log_info(msg: str, path: Path):
            if slient:
                return
            logging.info(f"{fn_name:<18} {msg} {path}")

        for kwarg in ("result_path",):
            assert kwarg in kwargs, f"Missing '{kwarg}' in kwargs for {fn_name}"

        overwrite: bool = kwargs.pop("overwrite", False)
        slient: bool = kwargs.pop("slient", False)
        result_path: Path = kwargs.pop("result_path")

        if not overwrite and result_path.exists():
            log_info(f"{TermColor.WARNING}Skipped{TermColor.ENDC}", result_path)
            return

        tmp_path = result_path.parent / f"{result_path.name}.tmp"
        tmp_path.unlink(missing_ok=True)
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        log_info(f"{TermColor.OKBLUE}Writing{TermColor.ENDC}", result_path)
        fn(*args, **kwargs, result_path=tmp_path)
        tmp_path.rename(result_path)
        log_info(f"{TermColor.OKGREEN}Written{TermColor.ENDC}", result_path)

    return wrapper


__all__ = ["manage_result_path"]
