"""Shared plot style, colors, and axis formatters for benchmark plots."""

from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Colorblind-friendly palette: sequential first, then parallel process counts
# (same index = same "variant" across plots)
PALETTE = [
    "#0173B2",  # blue (sequential)
    "#E64B35",  # red
    "#029E73",  # green
    "#DE8F05",  # orange
    "#CC78BC",  # purple
    "#CA9161",  # brown
    "#FBAFE4",  # pink
    "#949494",  # gray
]
FIG_SIZE = (10, 6.5)
DPI = 200
GRID_ALPHA = 0.4


def apply_plot_style() -> None:
    """Set matplotlib rcParams for readable, consistent benchmark plots."""
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["legend.fontsize"] = 10


def color_for_sequential() -> str:
    """Color for the sequential series."""
    return PALETTE[0]


def color_for_process_count(index: int) -> str:
    """Color for parallel series by index (0 = first process count, e.g. 2)."""
    return PALETTE[1 + (index % (len(PALETTE) - 1))]


def color_for_size_index(index: int) -> str:
    """Color for series by size index (e.g. highlight_sizes)."""
    return PALETTE[index % len(PALETTE)]


def format_size_axis(ax: plt.Axes) -> None:
    """Format x-axis with log-scale input sizes as human-readable (16K, 1M)."""
    ax.xaxis.set_major_formatter(SizeFormatter())


class SizeFormatter(mticker.ScalarFormatter):
    """Format integers as 16K, 256K, 1M etc. for log-scale size axes."""

    def __init__(self) -> None:
        super().__init__()
        self.set_scientific(False)

    def __call__(self, x: float, pos: int | None = None) -> str:
        if x <= 0:
            return "0"
        n = int(round(x))
        if n >= 1_000_000:
            return f"{n // 1_000_000}M"
        if n >= 1_000:
            return f"{n // 1_000}K"
        return str(n)
