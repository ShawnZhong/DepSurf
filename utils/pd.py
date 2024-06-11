import pandas as pd


def setup_pandas():
    # https://pandas.pydata.org/docs/reference/api/pandas.set_option.html
    pd.set_option("display.min_rows", 500)
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 100)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", 1000)


setup_pandas()
