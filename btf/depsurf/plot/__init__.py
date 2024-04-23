import matplotlib as mpl
from depsurf.setup import setup_pandas

from .utils import *

# https://matplotlib.org/stable/api/matplotlib_configuration_api.html#default-values-and-styling
mpl.rcParams["figure.dpi"] = 200
mpl.rcParams["figure.figsize"] = (10, 5)
mpl.rcParams["axes.xmargin"] = 0.01
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False
mpl.rcParams["legend.frameon"] = False

setup_pandas()
