import logging
import pickle
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import transforms

from depsurf.paths import OUTPUT_PATH, PROJ_PATH

FIG_PATH = PROJ_PATH / "paper" / "figs"
TAB_PATH = PROJ_PATH / "paper" / "tabs"


#
# Matplotlib
#


def setup_matplotlib():
    # https://matplotlib.org/stable/api/matplotlib_configuration_api.html#default-values-and-styling
    plt.rcParams["figure.dpi"] = 200
    plt.rcParams["figure.figsize"] = (10, 5)
    plt.rcParams["axes.xmargin"] = 0.01
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["legend.frameon"] = False


setup_matplotlib()


def bold(text):
    return f"$\\mathbf{{{text}}}$"


def get_text_height(ax: plt.Axes):
    from matplotlib.text import Text

    text = Text(text="0", figure=ax.figure)
    return text.get_window_extent().height


def get_legend_handles_labels(arg):
    if isinstance(arg, plt.Axes):
        axes = [arg]
    elif isinstance(arg, plt.Figure):
        axes = arg.axes
    labels_handles = {
        label: handle
        for ax in axes
        for handle, label in zip(*ax.get_legend_handles_labels())
    }.items()
    labels, handles = zip(*labels_handles)
    return handles, labels


def plot_yticks(ax: plt.Axes):
    locator = plt.MaxNLocator(nbins="auto", steps=[1, 2, 4, 5, 10])
    ax.yaxis.set_major_locator(locator)
    yticks = ax.get_yticks()
    if all(y % 1000 == 0 for y in yticks):
        fn = lambda x, _: f"{x / 1000:.0f}k" if x != 0 else "0"
    elif all(y % 100 == 0 for y in yticks) and max(yticks) > 1000:
        fn = lambda x, _: f"{x / 1000:.1f}k" if x != 0 else "0"
    else:
        fn = lambda x, _: f"{x:.0f}"
    ax.yaxis.set_major_formatter(plt.FuncFormatter(fn))


def label_multiline_text(ax: plt.Axes, x, y, lines, colors=None, fontsize=8):
    if colors is None:
        colors = [None for _ in lines]
    for i, (line, color) in enumerate(zip(lines, colors)):
        ax.text(
            x,
            y,
            line,
            color=color,
            fontsize=fontsize,
            ha="center",
            va="top",
            transform=transforms.offset_copy(
                ax.transData, y=-fontsize * i, units="dots"
            ),
        )


def save_fig(fig: plt.Figure, name: str, close=True):
    path = FIG_PATH / f"{name}.pdf"
    path.unlink(missing_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0)
    logging.info(f"Saved figure to {path}")
    if close:
        plt.close(fig)


def plot_bar(ax: plt.Axes, df: pd.DataFrame, columns=None):
    xs = np.arange(len(df))
    bottom = np.zeros(len(df))
    for col in df.columns if columns is None else columns:
        ax.bar(xs, df[col], bottom=bottom, label=col, color=col.color)
        bottom += df[col]

    return bottom


#
# Pandas
#


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


def save_df(
    df: pd.DataFrame, name: str, path: Path = OUTPUT_PATH, return_df=True
) -> Optional[pd.DataFrame]:
    save_df_txt(df, path=path / f"{name}.txt")
    save_df_pkl(df, path=path / f"{name}.pkl")
    if return_df:
        return df


def load_df(name, path=None) -> pd.DataFrame:
    if path is None:
        path = OUTPUT_PATH

    filepath = path / f"{name}.pkl"
    df = pd.read_pickle(filepath)
    logging.info(f"Loaded df from {filepath}")

    return df


def dump_pkl(obj, name: str, path: Path = OUTPUT_PATH):
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{name}.pkl"
    with open(filepath, "wb") as f:
        pickle.dump(obj, f)
    logging.info(f"Saved {name} to {filepath}")


def load_pkl(name: str, path: Path = OUTPUT_PATH):
    filepath = path / f"{name}.pkl"
    logging.info(f"Loding {name} from {filepath}")
    with open(filepath, "rb") as f:
        return pickle.load(f)


#
# LaTeX
#


def save_latex(text: str, name: str, path: Path = TAB_PATH):
    text = text.replace("\\midrule\n\\bottomrule", "\\bottomrule")
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{name}.tex"
    with open(filepath, "w") as f:
        f.write(text)
    logging.info(f"Saved {name} to {filepath}")


def rotate_multirow(text: str):
    return re.sub(
        r"\\multirow\[t\]{(\d+)}{\*}{(.*?)}",
        r"\\multirow{\1}{*}{\\rotatebox[origin=c]{90}{\2}}",
        text,
    )


def replace_cline(text: str):
    return re.sub(r"\\cline{.*?}", r"\\midrule", text)


GRAY_DASH = r"\color{lightgray}{-}"
