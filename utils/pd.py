import os


def setup_pandas():
    os.environ["NUMEXPR_NUM_THREADS"] = "1"

    import pandas as pd

    # https://pandas.pydata.org/docs/reference/api/pandas.set_option.html
    pd.set_option("display.min_rows", 500)
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 100)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", 1000)


setup_pandas()
