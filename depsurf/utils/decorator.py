import logging

from pathlib import Path


def check_result_path(fn: callable):
    def wrapper(*args, **kwargs):
        fn_name = fn.__name__

        for kwarg in ("overwrite", "result_path"):
            assert kwarg in kwargs, f"Missing '{kwarg}' in kwargs for {fn_name}"

        overwrite = kwargs.pop("overwrite")
        slient = kwargs.pop("slient", False)
        result_path = Path(kwargs["result_path"])

        if not overwrite and result_path.exists() and result_path.stat().st_size > 0:
            if not slient:
                logging.info(f"{fn_name:<16} Using {result_path}")
            return
        result_path.parent.mkdir(parents=True, exist_ok=True)
        return fn(*args, **kwargs)

    return wrapper
