import logging
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib import transforms
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter, MaxNLocator

from .paths import FIG_PATH


def setup_matplotlib():
    # https://matplotlib.org/stable/api/matplotlib_configuration_api.html#default-values-and-styling
    plt.rcParams["figure.dpi"] = 200
    plt.rcParams["figure.figsize"] = (10, 5)
    plt.rcParams["axes.xmargin"] = 0.01
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["legend.frameon"] = False


setup_matplotlib()


def get_text_height(ax: Axes):
    text = Text(text="0", figure=ax.figure)
    return text.get_window_extent().height


def get_legend_handles_labels(arg):
    if isinstance(arg, Axes):
        axes = [arg]
    elif isinstance(arg, Figure):
        axes = arg.axes
    labels_handles = {
        label: handle
        for ax in axes
        for handle, label in zip(*ax.get_legend_handles_labels())
    }.items()
    labels, handles = zip(*labels_handles)
    return handles, labels


def format_yticks(ax: Axes):
    locator = MaxNLocator(nbins="auto", steps=[1, 2, 4, 5, 10])
    ax.yaxis.set_major_locator(locator)
    yticks = ax.get_yticks()
    if all(y % 1000 == 0 for y in yticks):
        fn = lambda x, _: f"{x / 1000:.0f}k" if x != 0 else "0"
    elif all(y % 100 == 0 for y in yticks) and max(yticks) > 1000:
        fn = lambda x, _: f"{x / 1000:.1f}k" if x != 0 else "0"
    else:
        fn = lambda x, _: f"{x:.0f}"
    ax.yaxis.set_major_formatter(FuncFormatter(fn))


def label_multiline_text(ax: Axes, x, y, lines, colors=None, fontsize=8):
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


def save_fig(fig: Figure, name: str, path: Path = FIG_PATH):
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{name}.pdf"
    filepath.unlink(missing_ok=True)
    fig.savefig(filepath, bbox_inches="tight", pad_inches=0)
    logging.info(f"Saved figure to {filepath}")
