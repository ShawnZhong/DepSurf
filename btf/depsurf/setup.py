import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(filename)12s:%(lineno)-3d] %(levelname)s: %(message)s",
    )


def setup_pandas():
    import pandas as pd

    # https://pandas.pydata.org/docs/reference/api/pandas.set_option.html
    pd.set_option("display.min_rows", 300)
    pd.set_option("display.max_rows", 300)
    pd.set_option("display.max_columns", 100)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", 1000)


def reload_depsurf():
    import sys
    from importlib import reload

    for k in list(sys.modules.keys()):
        if k.startswith("depsurf"):
            del sys.modules[k]

    import depsurf

    reload(depsurf)
