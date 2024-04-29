import logging
from pathlib import Path
import json

import pandas as pd
from depsurf.paths import OUTPUT_PATH


def setup_pandas():
    # https://pandas.pydata.org/docs/reference/api/pandas.set_option.html
    pd.set_option("display.min_rows", 500)
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 100)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", 1000)


setup_pandas()


def save_df(df: pd.DataFrame, name, path=None):
    assert isinstance(name, str)
    if path is None:
        path = OUTPUT_PATH
    else:
        assert isinstance(path, Path)

    filepath = path / f"{name}.pkl"
    df.to_pickle(filepath)
    logging.info(f"Saved dataframe to {filepath}")

    filepath = path / f"{name}.txt"
    df.to_string(filepath)
    logging.info(f"Saved dataframe to {filepath}")

    return df


def load_df(name, path=None):
    if path is None:
        path = OUTPUT_PATH

    filepath = path / f"{name}.pkl"
    df = pd.read_pickle(filepath)
    logging.info(f"Loaded df from {filepath}")

    return df
