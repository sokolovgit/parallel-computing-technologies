from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PALETTE = [
    "#0173B2",
    "#E64B35",
    "#029E73",
    "#DE8F05",
    "#CC78BC",
    "#CA9161",
    "#FBAFE4",
    "#949494",
]
FIG_SIZE = (10, 6.5)
DPI = 200
GRID_ALPHA = 0.4


def apply_plot_style() -> None:
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["legend.fontsize"] = 10


def color_for_sequential() -> str:
    return PALETTE[0]


def color_for_process_count(index: int) -> str:
    return PALETTE[1 + (index % (len(PALETTE) - 1))]


def color_for_size_index(index: int) -> str:
    return PALETTE[index % len(PALETTE)]


def format_size_axis(ax: plt.Axes) -> None:
    ax.xaxis.set_major_formatter(SizeFormatter())


class SizeFormatter(mticker.ScalarFormatter):
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


def format_time_axis(ax: plt.Axes) -> None:
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_time_tick_label))


def _time_tick_label(x: float, pos: int | None) -> str:
    if x <= 0:
        return "0"
    if x >= 100:
        return f"{int(round(x))}"
    if x >= 1:
        return f"{x:.1f}".rstrip("0").rstrip(".")
    if x >= 0.1:
        return f"{x:.2f}".rstrip("0").rstrip(".")
    if x >= 0.01:
        return f"{x:.3f}".rstrip("0").rstrip(".")
    return f"{x:.4f}".rstrip("0").rstrip(".")
