import logging

from depsurf.paths import FIG_PATH
from matplotlib import pyplot as plt


def bold(text):
    return f"$\\mathbf{{{text}}}$"


def get_text_height(ax: plt.Axes):
    from matplotlib.text import Text

    text = Text(text="0", figure=ax.figure)
    return text.get_window_extent().height


def get_legend_handles_labels(fig: plt.Figure):
    labels_handles = {
        label: handle
        for ax in fig.axes
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


def save_fig(fig: plt.Figure, name: str):
    path = FIG_PATH / f"{name}.pdf"
    fig.savefig(path, bbox_inches="tight", pad_inches=0)
    logging.info(f"Saved figure to {path}")
    plt.close(fig)
