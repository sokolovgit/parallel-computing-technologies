from __future__ import annotations

import matplotlib.pyplot as plt

from benchmark.models import BenchmarkResult
from benchmark.plot_style import (
    DPI,
    FIG_SIZE,
    GRID_ALPHA,
    apply_plot_style,
    color_for_process_count,
    color_for_sequential,
    color_for_size_index,
    format_size_axis,
    format_time_axis,
)
from benchmark.stats import HAS_RESOURCE, speedup_ci_half


def _add_series_ci(
    ax: plt.Axes,
    x: list[int] | list[float],
    meds: list[float],
    errs: list[float],
    label: str,
    color: str,
    marker: str = "o",
) -> None:
    ax.errorbar(
        x,
        meds,
        yerr=errs,
        marker=marker,
        label=label,
        linewidth=2,
        capsize=2,
        color=color,
    )


def _finish_axes(
    ax: plt.Axes,
    xlabel: str,
    ylabel: str,
    title: str,
    *,
    log_x: bool = False,
    log_y: bool = False,
    size_axis: bool = False,
    y_min: float | None = None,
    ref_line: tuple[float, str] | None = None,
) -> None:
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_x:
        ax.set_xscale("log", base=2)
    if log_y:
        ax.set_yscale("log")
        format_time_axis(ax)
    if size_axis:
        format_size_axis(ax)
    if y_min is not None:
        ax.set_ylim(bottom=y_min)
    if ref_line is not None:
        y_val, ref_label = ref_line
        ax.axhline(
            y=y_val,
            color="gray",
            linestyle="--",
            alpha=0.7,
            label=ref_label,
        )
    ax.legend(loc="best")
    ax.grid(True, alpha=GRID_ALPHA, linestyle="-")


class PlotGenerator:
    def __init__(
        self,
        result: BenchmarkResult,
        formats: list[str] | None = None,
    ) -> None:
        self._result = result
        self._dir = result.results_dir
        self._formats = formats if formats is not None else ["png"]

    def _save_fig(self, fig: plt.Figure, base_name: str) -> None:
        for ext in self._formats:
            ext = ext.lower().strip()
            if not ext.startswith("."):
                ext = f".{ext}"
            path = self._dir / f"{base_name}{ext}"
            fig.savefig(path, dpi=DPI)
            print(f"  Saved {path}")
        plt.close(fig)

    def plot_execution_time(self) -> None:
        result = self._result
        sizes = sorted(result.sequential_times.keys())
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        seq_meds = [result.sequential_times[s] for s in sizes]
        seq_errs = [
            result.sequential_stats[s].ci_half if s in result.sequential_stats else 0.0
            for s in sizes
        ]
        _add_series_ci(
            ax, sizes, seq_meds, seq_errs, "Послідовний", color_for_sequential()
        )
        for idx, nprocs in enumerate(sorted(result.parallel_times.keys())):
            meds = [result.parallel_times[nprocs][s] for s in sizes]
            errs = [
                result.parallel_stats.get(nprocs, {}).get(s)
                and result.parallel_stats[nprocs][s].ci_half
                or 0.0
                for s in sizes
            ]
            _add_series_ci(
                ax,
                sizes,
                meds,
                errs,
                f"Паралельний ({nprocs} процесів)",
                color_for_process_count(idx),
                marker="s",
            )
        _finish_axes(
            ax,
            "Розмір вхідних даних (n)",
            "Час (сек)",
            "Час виконання залежно від розміру вхідних даних (медіана ± 95%)",
            log_x=True,
            log_y=True,
            size_axis=True,
        )
        fig.tight_layout()
        self._save_fig(fig, "execution_time")

    def plot_speedup(self) -> None:
        result = self._result
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        for idx, nprocs in enumerate(sorted(result.speedup.keys())):
            sizes = sorted(result.speedup[nprocs].keys())
            sp_meds = [result.speedup[nprocs][s] for s in sizes]
            sp_errs = []
            for s in sizes:
                seq_st = result.sequential_stats.get(s)
                par_st = result.parallel_stats.get(nprocs, {}).get(s)
                sp_errs.append(
                    speedup_ci_half(seq_st, par_st) if seq_st and par_st else 0.0
                )
            _add_series_ci(
                ax,
                sizes,
                sp_meds,
                sp_errs,
                f"{nprocs} процесів",
                color_for_process_count(idx),
                marker="s",
            )
        _finish_axes(
            ax,
            "Розмір вхідних даних (n)",
            "Прискорення (T_seq / T_par)",
            "Прискорення залежно від розміру даних",
            log_x=True,
            size_axis=True,
            ref_line=(1.0, "Без прискорення"),
        )
        fig.tight_layout()
        self._save_fig(fig, "speedup_vs_size")

    def plot_speedup_vs_processes(
        self, highlight_sizes: list[int] | None = None
    ) -> None:
        result = self._result
        all_sizes = sorted(next(iter(result.speedup.values())).keys())
        if highlight_sizes is None:
            highlight_sizes = [all_sizes[len(all_sizes) // 2], all_sizes[-1]]
        nprocs_list = sorted(result.speedup.keys())
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        for idx, size in enumerate(highlight_sizes):
            sp_meds = [result.speedup[np_][size] for np_ in nprocs_list]
            sp_errs = []
            seq_st = result.sequential_stats.get(size)
            for np_ in nprocs_list:
                par_st = result.parallel_stats.get(np_, {}).get(size)
                sp_errs.append(
                    speedup_ci_half(seq_st, par_st) if seq_st and par_st else 0.0
                )
            _add_series_ci(
                ax,
                nprocs_list,
                sp_meds,
                sp_errs,
                f"n = {size:,}",
                color_for_size_index(idx),
            )
        ax.set_xticks(nprocs_list)
        _finish_axes(
            ax,
            "Кількість процесів (P)",
            "Прискорення (T_seq / T_par)",
            "Прискорення залежно від кількості процесів",
            ref_line=(1.0, "Без прискорення"),
        )
        fig.tight_layout()
        self._save_fig(fig, "speedup_vs_processes")

    def plot_efficiency(self) -> None:
        result = self._result
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        for idx, nprocs in enumerate(sorted(result.efficiency.keys())):
            sizes = sorted(result.efficiency[nprocs].keys())
            eff_meds = [result.efficiency[nprocs][s] for s in sizes]
            eff_errs = []
            for s in sizes:
                seq_st = result.sequential_stats.get(s)
                par_st = result.parallel_stats.get(nprocs, {}).get(s)
                sp_ci = speedup_ci_half(seq_st, par_st) if seq_st and par_st else 0.0
                eff_errs.append(sp_ci / nprocs if nprocs else 0.0)
            _add_series_ci(
                ax,
                sizes,
                eff_meds,
                eff_errs,
                f"{nprocs} процесів",
                color_for_process_count(idx),
                marker="s",
            )
        _finish_axes(
            ax,
            "Розмір вхідних даних (n)",
            "Ефективність (прискорення / P)",
            "Ефективність паралелізації (теоретичний максимум = 1)",
            log_x=True,
            size_axis=True,
            y_min=0,
            ref_line=(1.0, "Ідеально (ефективність = 1)"),
        )
        fig.tight_layout()
        self._save_fig(fig, "efficiency")

    def plot_cpu_utilization(self) -> None:
        if not HAS_RESOURCE or not self._result.parallel_metrics:
            return
        result = self._result
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        for idx, nprocs in enumerate(sorted(result.parallel_metrics.keys())):
            sizes = sorted(result.parallel_metrics[nprocs].keys())
            utils = [
                result.parallel_metrics[nprocs][s].cpu_utilization(nprocs)
                if result.parallel_metrics[nprocs][s]
                else 0.0
                for s in sizes
            ]
            ax.plot(
                sizes,
                utils,
                marker="s",
                label=f"{nprocs} процесів",
                linewidth=2,
                color=color_for_process_count(idx),
            )
        _finish_axes(
            ax,
            "Розмір вхідних даних (n)",
            "Завантаження CPU (сума CPU дочірніх процесів / (час·P))",
            "Завантаження CPU при паралельному виконанні",
            log_x=True,
            size_axis=True,
            y_min=0,
            ref_line=(1.0, "Ідеально (завантаження = 1)"),
        )
        fig.tight_layout()
        self._save_fig(fig, "cpu_utilization")

    def plot_sequential_analysis(self) -> None:
        result = self._result
        sizes = sorted(result.sequential_times.keys())
        if not sizes:
            return
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        seq_meds = [result.sequential_times[s] for s in sizes]
        seq_errs = [
            result.sequential_stats[s].ci_half if s in result.sequential_stats else 0.0
            for s in sizes
        ]
        _add_series_ci(
            ax, sizes, seq_meds, seq_errs, "Послідовний", color_for_sequential()
        )
        _finish_axes(
            ax,
            "Розмір вхідних даних (n)",
            "Час (сек)",
            "Послідовна реалізація: залежність часу виконання від розміру даних",
            log_x=True,
            log_y=True,
            size_axis=True,
        )
        fig.tight_layout()
        self._save_fig(fig, "sequential_analysis")

    def generate_all(self) -> None:
        apply_plot_style()
        self.plot_sequential_analysis()
        self.plot_execution_time()
        self.plot_speedup()
        self.plot_speedup_vs_processes()
        self.plot_efficiency()
        self.plot_cpu_utilization()
