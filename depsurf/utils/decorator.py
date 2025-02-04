import logging
from pathlib import Path


def manage_result_path(fn):
    def wrapper(*args, **kwargs):
        fn_name = fn.__name__

        for kwarg in ("result_path",):
            assert kwarg in kwargs, f"Missing '{kwarg}' in kwargs for {fn_name}"

        overwrite: bool = kwargs.pop("overwrite", False)
        slient: bool = kwargs.pop("slient", False)
        result_path: Path = kwargs.pop("result_path")

        if not overwrite and result_path.exists():
            if not slient:
                logging.info(f"{fn_name:<16} Using {result_path}")
            return

        tmp_path = result_path.parent / f"{result_path.name}.tmp"
        tmp_path.unlink(missing_ok=True)
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        result = fn(*args, **kwargs, result_path=tmp_path)
        tmp_path.rename(result_path)

        if not slient:
            logging.info(f"{fn_name:<16} Saved {result_path}")
        return result

    return wrapper
