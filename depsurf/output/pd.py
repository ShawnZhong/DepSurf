import logging
from pathlib import Path

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


def save_df_txt(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_string(path)
    logging.info(f"Saved dataframe to {path}")

    return df


def save_df_pkl(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

    df.to_pickle(path)
    logging.info(f"Saved dataframe to {path}")

    return df


def save_df(df: pd.DataFrame, name: str, path: Path = OUTPUT_PATH):
    save_df_txt(df, path=path / f"{name}.txt")
    save_df_pkl(df, path=path / f"{name}.pkl")
    return df


def load_df(name, path=None) -> pd.DataFrame:
    if path is None:
        path = OUTPUT_PATH

    filepath = path / f"{name}.pkl"
    df = pd.read_pickle(filepath)
    logging.info(f"Loaded df from {filepath}")

    return df
