# ДОДАТОК В. Код бенчмарку

У додатку наведено модулі пакета `benchmark` без коментарів (каталог `course-work/project/benchmark/`). Запуск повного циклу вимірювання: з каталогу `project` виконати `python -m benchmark` (потрібні залежності: `numpy`, `matplotlib`).

## В.1. Пакет `benchmark` (`__init__.py`)

```python
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from benchmark.config import BenchmarkConfig
from benchmark.models import BenchmarkResult, SystemMetrics
from benchmark.runner import BenchmarkRunner
from benchmark.stats import RunStats

__all__ = [
    "BenchmarkConfig",
    "BenchmarkResult",
    "BenchmarkRunner",
    "RunStats",
    "SystemMetrics",
]

```

## В.2. `config.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def parse_sizes(spec: str) -> list[int]:
    spec = spec.strip()
    if ":" in spec:
        lo_str, hi_str = spec.split(":", 1)
        lo = int(lo_str.strip())
        hi = int(hi_str.strip())
        return [2**k for k in range(lo, hi + 1)]
    return [int(x.strip()) for x in spec.split(",") if x.strip()]


def parse_processes(spec: str) -> list[int]:
    return [int(x.strip()) for x in spec.split(",") if x.strip()]


@dataclass(frozen=True)
class BenchmarkConfig:
    sizes: list[int]
    process_counts: list[int]
    num_runs: int
    warmup_runs: int
    results_dir: Path
    disable_gc: bool
    drop_outliers: bool
    plot_formats: list[str]

    @classmethod
    def default(cls, results_dir: Path | None = None) -> BenchmarkConfig:
        base = Path(__file__).resolve().parent.parent / "results"
        return cls(
            sizes=[2**k for k in range(10, 20)],
            process_counts=[2, 4, 8],
            num_runs=5,
            warmup_runs=2,
            results_dir=results_dir or base,
            disable_gc=True,
            drop_outliers=False,
            plot_formats=["png"],
        )

```

## В.3. `stats.py`

```python
from __future__ import annotations

import math
import statistics
import sys
from dataclasses import dataclass

try:
    import resource

    HAS_RESOURCE = hasattr(resource, "getrusage") and sys.platform != "win32"
except ImportError:
    HAS_RESOURCE = False


@dataclass(frozen=True)
class RunStats:
    median: float
    mean: float
    stdev: float
    ci_half: float

    @property
    def ci_low(self) -> float:
        return max(0.0, self.median - self.ci_half)

    @property
    def ci_high(self) -> float:
        return self.median + self.ci_half


def filter_outliers_iqr(times: list[float], factor: float = 1.5) -> list[float]:
    if len(times) < 4:
        return list(times)
    sorted_times = sorted(times)
    n = len(sorted_times)
    q1_idx = n // 4
    q3_idx = (3 * n) // 4
    q1 = sorted_times[q1_idx]
    q3 = sorted_times[q3_idx]
    iqr = q3 - q1
    if iqr <= 0:
        return list(times)
    low = q1 - factor * iqr
    high = q3 + factor * iqr
    return [t for t in times if low <= t <= high]


def compute_stats(times: list[float]) -> RunStats:
    if not times:
        return RunStats(median=0.0, mean=0.0, stdev=0.0, ci_half=0.0)
    n = len(times)
    median = statistics.median(times)
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if n >= 2 else 0.0
    ci_half = (1.96 * stdev / math.sqrt(n)) if n >= 2 else 0.0
    return RunStats(median=median, mean=mean, stdev=stdev, ci_half=ci_half)


def speedup_ci_half(seq_stats: RunStats, par_stats: RunStats) -> float:
    if par_stats.median <= 0:
        return 0.0
    a = seq_stats.ci_half / par_stats.median
    b = (seq_stats.median * par_stats.ci_half) / (par_stats.median * par_stats.median)
    return math.sqrt(a * a + b * b)


def rss_mb(ru_maxrss: float) -> float:
    if sys.platform == "darwin":
        return ru_maxrss / (1024 * 1024)
    return ru_maxrss / 1024

```

## В.4. `models.py`

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.stats import RunStats, compute_stats


@dataclass
class SystemMetrics:
    wall_s: float
    cpu_self_s: float
    cpu_children_s: float
    rss_mb: float
    ctx_voluntary: int
    ctx_involuntary: int

    def cpu_utilization(self, nprocs: int) -> float:
        if nprocs <= 0:
            return 0.0
        ideal = self.wall_s * nprocs
        return self.cpu_children_s / ideal if ideal > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "wall_s": round(self.wall_s, 6),
            "cpu_self_s": round(self.cpu_self_s, 6),
            "cpu_children_s": round(self.cpu_children_s, 6),
            "rss_mb": round(self.rss_mb, 4),
            "ctx_voluntary": self.ctx_voluntary,
            "ctx_involuntary": self.ctx_involuntary,
        }


@dataclass
class BenchmarkResult:
    sequential_run_times: dict[int, list[float]] = field(default_factory=dict)
    parallel_run_times: dict[int, dict[int, list[float]]] = field(default_factory=dict)
    sequential_times: dict[int, float] = field(default_factory=dict)
    parallel_times: dict[int, dict[int, float]] = field(default_factory=dict)
    sequential_stats: dict[int, RunStats] = field(default_factory=dict)
    parallel_stats: dict[int, dict[int, RunStats]] = field(default_factory=dict)
    sequential_metrics: dict[int, SystemMetrics | None] = field(default_factory=dict)
    parallel_metrics: dict[int, dict[int, SystemMetrics | None]] = field(
        default_factory=dict
    )
    speedup: dict[int, dict[int, float]] = field(default_factory=dict)
    efficiency: dict[int, dict[int, float]] = field(default_factory=dict)
    results_dir: Path = Path("results")
    baseline_times: dict[int, float] = field(default_factory=dict)
    baseline_stats: dict[int, RunStats] = field(default_factory=dict)
    weak_scaling_sequential_times: dict[int, float] = field(default_factory=dict)
    weak_scaling_parallel_times: dict[int, float] = field(default_factory=dict)
    weak_scaling_sequential_stats: dict[int, RunStats] = field(default_factory=dict)
    weak_scaling_parallel_stats: dict[int, RunStats] = field(default_factory=dict)

    def _derive_times_and_stats(self) -> None:
        for size, times in self.sequential_run_times.items():
            if times:
                st = compute_stats(times)
                self.sequential_stats[size] = st
                self.sequential_times[size] = st.median
        for nprocs, size_map in self.parallel_run_times.items():
            self.parallel_stats.setdefault(nprocs, {})
            for size, times in size_map.items():
                if times:
                    st = compute_stats(times)
                    self.parallel_stats[nprocs][size] = st
                    if nprocs not in self.parallel_times:
                        self.parallel_times[nprocs] = {}
                    self.parallel_times[nprocs][size] = st.median

    def compute_metrics(self) -> None:
        if self.sequential_run_times or self.parallel_run_times:
            self._derive_times_and_stats()
        self.speedup = {}
        self.efficiency = {}
        for nprocs, size_map in self.parallel_times.items():
            self.speedup[nprocs] = {}
            self.efficiency[nprocs] = {}
            for size, par_t in size_map.items():
                seq_t = self.sequential_times.get(size, 0.0)
                sp = seq_t / par_t if par_t > 0 else 0.0
                self.speedup[nprocs][size] = sp
                self.efficiency[nprocs][size] = sp / nprocs

```

## В.5. `plot_style.py`

```python
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

```

## В.6. `plots.py`

```python
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

```

## В.7. `export.py`

```python
from __future__ import annotations

import csv
import json
import multiprocessing as mp
import platform
import sys
from datetime import UTC, datetime
from typing import Any

from benchmark.models import BenchmarkResult
from benchmark.stats import HAS_RESOURCE


def _json_metadata() -> dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "cpu_count": mp.cpu_count(),
        "platform": platform.platform(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def save_equipment_file(result: BenchmarkResult) -> None:
    meta = _json_metadata()
    path = result.results_dir / "equipment.txt"
    lines = [
        "Обладнання для тестування:",
        f"  Платформа: {meta['platform']}",
        f"  Кількість ядер CPU: {meta['cpu_count']}",
        f"  Python: {meta['python_version']}",
        f"  Дата та час: {meta['timestamp']}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Saved {path}")


def print_table(result: BenchmarkResult) -> None:
    sizes = sorted(result.sequential_times.keys())
    nprocs_list = sorted(result.parallel_times.keys())
    col_w = 14

    header = f"{'Size':>{col_w}}" + f"{'Sequential':>{col_w}}"
    for np_ in nprocs_list:
        header += f"{f'Par{np_}':>{col_w}}"
    header += f"{'Best Sp':>{col_w}}"
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for size in sizes:
        seq_t = result.sequential_times[size]
        row = f"{size:>{col_w},}" + f"{seq_t:>{col_w}.4f}"
        best_sp = 0.0
        for np_ in nprocs_list:
            par_t = result.parallel_times[np_][size]
            sp = result.speedup[np_][size]
            best_sp = max(best_sp, sp)
            row += f"{par_t:>{col_w}.4f}"
        row += f"{best_sp:>{col_w}.3f}x"
        print(row)
    print(sep)


def save_csv(result: BenchmarkResult) -> None:
    sizes = sorted(result.sequential_times.keys())
    nprocs_list = sorted(result.parallel_times.keys())
    path = result.results_dir / "benchmark_times.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        header = [
            "size",
            "sequential_median_s",
            "sequential_ci_half",
        ]
        for np_ in nprocs_list:
            header.extend(
                [
                    f"P{np_}_median_s",
                    f"P{np_}_ci_half",
                    f"P{np_}_speedup",
                    f"P{np_}_efficiency",
                ]
            )
        w.writerow(header)
        for size in sizes:
            seq_st = result.sequential_stats.get(size)
            row = [
                size,
                result.sequential_times[size],
                seq_st.ci_half if seq_st else 0.0,
            ]
            for np_ in nprocs_list:
                par_st = result.parallel_stats.get(np_, {}).get(size)
                row.extend(
                    [
                        result.parallel_times[np_][size],
                        par_st.ci_half if par_st else 0.0,
                        result.speedup[np_][size],
                        result.efficiency[np_][size],
                    ]
                )
            w.writerow(row)
    print(f"  Saved {path}")


def save_latex_table(result: BenchmarkResult) -> None:
    sizes = sorted(result.sequential_times.keys())
    nprocs_list = sorted(result.parallel_times.keys())
    path = result.results_dir / "table.tex"
    lines = [
        r"\begin{tabular}{r|r|" + "r" * (2 * len(nprocs_list)) + "}",
        r"\hline",
        "Size & Sequential (s) & "
        + " & ".join(f"P={np_} (s)" for np_ in nprocs_list)
        + " & "
        + " & ".join(f"Speedup P={np_}" for np_ in nprocs_list)
        + r" \\",
        r"\hline",
    ]
    for size in sizes:
        cells = [
            f"{size:,}",
            f"{result.sequential_times[size]:.4f}",
        ]
        for np_ in nprocs_list:
            cells.append(f"{result.parallel_times[np_][size]:.4f}")
        for np_ in nprocs_list:
            cells.append(f"{result.speedup[np_][size]:.2f}")
        lines.append(" & ".join(cells) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}"])
    path.write_text("\n".join(lines))
    print(f"  Saved {path}")


def _json_sequential(result: BenchmarkResult) -> dict[str, Any]:
    out: dict[str, Any] = {
        "sequential": {str(k): v for k, v in result.sequential_times.items()},
        "sequential_stats": {
            str(k): {
                "median": v.median,
                "mean": v.mean,
                "stdev": v.stdev,
                "ci_half": v.ci_half,
            }
            for k, v in result.sequential_stats.items()
        },
    }
    if result.sequential_run_times:
        out["sequential_run_times"] = {
            str(k): v for k, v in result.sequential_run_times.items()
        }
    if HAS_RESOURCE and result.sequential_metrics:
        out["sequential_metrics"] = {
            str(s): (m.to_dict() if m else None)
            for s, m in result.sequential_metrics.items()
        }
    return out


def _json_parallel(result: BenchmarkResult) -> dict[str, Any]:
    out: dict[str, Any] = {
        "parallel": {
            str(np_): {str(s): t for s, t in st.items()}
            for np_, st in result.parallel_times.items()
        },
        "parallel_stats": {
            str(np_): {
                str(s): {
                    "median": st.median,
                    "mean": st.mean,
                    "stdev": st.stdev,
                    "ci_half": st.ci_half,
                }
                for s, st in pst.items()
            }
            for np_, pst in result.parallel_stats.items()
        },
    }
    if result.parallel_run_times:
        out["parallel_run_times"] = {
            str(np_): {str(s): t for s, t in st.items()}
            for np_, st in result.parallel_run_times.items()
        }
    if HAS_RESOURCE and result.parallel_metrics:
        out["parallel_metrics"] = {
            str(np_): {str(s): (m.to_dict() if m else None) for s, m in smap.items()}
            for np_, smap in result.parallel_metrics.items()
        }
    return out


def _json_derived(result: BenchmarkResult) -> dict[str, Any]:
    data: dict[str, Any] = {
        "speedup": {
            str(np_): {str(s): round(sp, 4) for s, sp in smap.items()}
            for np_, smap in result.speedup.items()
        },
        "efficiency": {
            str(np_): {str(s): round(e, 4) for s, e in emap.items()}
            for np_, emap in result.efficiency.items()
        },
    }
    data["cpu_utilization"] = {}
    for np_ in result.parallel_metrics:
        data["cpu_utilization"][str(np_)] = {}
        for s, m in result.parallel_metrics[np_].items():
            data["cpu_utilization"][str(np_)][str(s)] = (
                round(m.cpu_utilization(np_), 4) if m else None
            )
    return data


def save_json(result: BenchmarkResult) -> None:
    data: dict[str, Any] = {
        "metadata": _json_metadata(),
        **_json_sequential(result),
        **_json_parallel(result),
        **_json_derived(result),
    }
    path = result.results_dir / "benchmark_data.json"
    path.write_text(json.dumps(data, indent=2))
    print(f"  Saved {path}")
    save_equipment_file(result)

```

## В.8. `load_result.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.models import BenchmarkResult, SystemMetrics
from benchmark.stats import RunStats


def _run_stats_from_dict(d: dict[str, Any]) -> RunStats:
    return RunStats(
        median=float(d["median"]),
        mean=float(d["mean"]),
        stdev=float(d["stdev"]),
        ci_half=float(d["ci_half"]),
    )


def _system_metrics_from_dict(d: dict[str, Any]) -> SystemMetrics:
    return SystemMetrics(
        wall_s=float(d["wall_s"]),
        cpu_self_s=float(d["cpu_self_s"]),
        cpu_children_s=float(d["cpu_children_s"]),
        rss_mb=float(d["rss_mb"]),
        ctx_voluntary=int(d["ctx_voluntary"]),
        ctx_involuntary=int(d["ctx_involuntary"]),
    )


def load_benchmark_result(path: Path) -> BenchmarkResult:
    if path.is_dir():
        data_path = path / "benchmark_data.json"
        results_dir = path
    else:
        data_path = path
        results_dir = path.parent

    with data_path.open(encoding="utf-8") as f:
        data = json.load(f)

    result = BenchmarkResult(results_dir=results_dir)

    seq = data.get("sequential") or {}
    result.sequential_times = {int(k): float(v) for k, v in seq.items()}

    seq_st = data.get("sequential_stats") or {}
    result.sequential_stats = {
        int(k): _run_stats_from_dict(v) for k, v in seq_st.items()
    }

    par = data.get("parallel") or {}
    result.parallel_times = {
        int(np_): {int(s): float(t) for s, t in st.items()} for np_, st in par.items()
    }

    par_st = data.get("parallel_stats") or {}
    result.parallel_stats = {
        int(np_): {int(s): _run_stats_from_dict(st) for s, st in pst.items()}
        for np_, pst in par_st.items()
    }

    sp = data.get("speedup") or {}
    result.speedup = {
        int(np_): {int(s): float(v) for s, v in smap.items()}
        for np_, smap in sp.items()
    }

    eff = data.get("efficiency") or {}
    result.efficiency = {
        int(np_): {int(s): float(v) for s, v in emap.items()}
        for np_, emap in eff.items()
    }

    par_metrics = data.get("parallel_metrics") or {}
    for np_, smap in par_metrics.items():
        result.parallel_metrics[int(np_)] = {}
        for s, m in smap.items():
            if m is None:
                result.parallel_metrics[int(np_)][int(s)] = None
            else:
                result.parallel_metrics[int(np_)][int(s)] = _system_metrics_from_dict(m)

    return result

```

## В.9. `runner.py`

```python
from __future__ import annotations

import gc
import statistics
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from benchmark.config import BenchmarkConfig
from benchmark.export import (
    print_table,
    save_csv,
    save_json,
    save_latex_table,
)
from benchmark.models import BenchmarkResult, SystemMetrics
from benchmark.plots import PlotGenerator
from benchmark.stats import (
    HAS_RESOURCE,
    RunStats,
    compute_stats,
    filter_outliers_iqr,
    rss_mb,
)

if TYPE_CHECKING:
    from bitonic import ParallelBitonicSorter, SequentialBitonicSorter

if HAS_RESOURCE:
    import resource


def run_trials(
    fn: Callable[[], None],
    *,
    warmup_runs: int,
    num_runs: int,
    drop_outliers: bool = False,
    disable_gc: bool = True,
    track_system_metrics: bool = False,
) -> tuple[list[float], RunStats, SystemMetrics | None]:
    for _ in range(warmup_runs):
        fn()
    walls: list[float] = []
    runs_metrics: list[SystemMetrics | None] = []
    for _ in range(num_runs):
        if disable_gc:
            gc.disable()
        if HAS_RESOURCE and track_system_metrics:
            r0 = resource.getrusage(resource.RUSAGE_SELF)
            r0c = resource.getrusage(resource.RUSAGE_CHILDREN)
            t0_wall = time.perf_counter()
            t0_cpu = time.process_time()
            fn()
            t1_wall = time.perf_counter()
            t1_cpu = time.process_time()
            r1 = resource.getrusage(resource.RUSAGE_SELF)
            r1c = resource.getrusage(resource.RUSAGE_CHILDREN)
            wall = t1_wall - t0_wall
            cpu_self = t1_cpu - t0_cpu
            cpu_children = (r1c.ru_utime + r1c.ru_stime) - (r0c.ru_utime + r0c.ru_stime)
            rss = rss_mb(r1.ru_maxrss)
            ctx_v = r1.ru_nvcsw - r0.ru_nvcsw
            ctx_i = r1.ru_nivcsw - r0.ru_nivcsw
            runs_metrics.append(
                _collect_system_metrics(wall, cpu_self, cpu_children, rss, ctx_v, ctx_i)
            )
            walls.append(wall)
        else:
            t0 = time.perf_counter()
            fn()
            walls.append(time.perf_counter() - t0)
        if disable_gc:
            gc.enable()
    rep_metric: SystemMetrics | None = None
    if HAS_RESOURCE and track_system_metrics and runs_metrics and walls:
        med = statistics.median(walls)
        idx = min(range(len(walls)), key=lambda i: abs(walls[i] - med))
        rep_metric = runs_metrics[idx]
    if drop_outliers and len(walls) >= 4:
        walls = filter_outliers_iqr(walls)
    stats = compute_stats(walls)
    return walls, stats, rep_metric


def _collect_system_metrics(
    wall_s: float,
    cpu_self_s: float,
    cpu_children_s: float,
    rss_mb_val: float,
    ctx_voluntary: int,
    ctx_involuntary: int,
) -> SystemMetrics:
    return SystemMetrics(
        wall_s=wall_s,
        cpu_self_s=cpu_self_s,
        cpu_children_s=cpu_children_s,
        rss_mb=rss_mb_val,
        ctx_voluntary=ctx_voluntary,
        ctx_involuntary=ctx_involuntary,
    )


class BenchmarkRunner:
    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        self._config = config or BenchmarkConfig.default()
        self._config.results_dir.mkdir(exist_ok=True)

    @staticmethod
    def _generate_array(size: int, seed: int = 42) -> NDArray[np.int64]:
        rng = np.random.default_rng(seed)
        return rng.integers(-100_000, 100_000, size=size, dtype=np.int64)

    def _measure(
        self,
        run_one: Callable[[], None],
        track_system_metrics: bool = False,
    ) -> tuple[list[float], RunStats, SystemMetrics | None]:
        return run_trials(
            run_one,
            warmup_runs=self._config.warmup_runs,
            num_runs=self._config.num_runs,
            drop_outliers=self._config.drop_outliers,
            disable_gc=self._config.disable_gc,
            track_system_metrics=track_system_metrics and HAS_RESOURCE,
        )

    def _measure_sequential(
        self,
        sorter: SequentialBitonicSorter,
        arr: NDArray[np.int64],
    ) -> tuple[list[float], RunStats, SystemMetrics | None]:
        from bitonic import SequentialBitonicSorter as _Seq

        assert isinstance(sorter, _Seq)
        return self._measure(lambda: sorter.sort(arr), track_system_metrics=False)

    def _measure_parallel(
        self,
        sorter: ParallelBitonicSorter,
        arr: NDArray[np.int64],
    ) -> tuple[list[float], RunStats, SystemMetrics | None]:
        from bitonic import ParallelBitonicSorter as _Par

        assert isinstance(sorter, _Par)
        return self._measure(lambda: sorter.sort(arr), track_system_metrics=True)

    def _bench_sequential(
        self,
    ) -> tuple[dict[int, list[float]], dict[int, SystemMetrics | None]]:
        from bitonic import SequentialBitonicSorter

        sorter = SequentialBitonicSorter()
        run_times: dict[int, list[float]] = {}
        metrics: dict[int, SystemMetrics | None] = {}
        for size in self._config.sizes:
            arr = self._generate_array(size)
            walls, st, m = self._measure_sequential(sorter, arr)
            run_times[size] = walls
            metrics[size] = m
            print(
                f"  Sequential  n={size:>8,}  "
                f"median={st.median:.4f}s  ±{st.ci_half:.4f}s"
            )
        return run_times, metrics

    def _bench_parallel(
        self,
    ) -> tuple[
        dict[int, dict[int, list[float]]],
        dict[int, dict[int, SystemMetrics | None]],
    ]:
        from bitonic import ParallelBitonicSorter

        run_times: dict[int, dict[int, list[float]]] = {}
        metrics: dict[int, dict[int, SystemMetrics | None]] = {}
        for nprocs in self._config.process_counts:
            run_times[nprocs] = {}
            metrics[nprocs] = {}
            sorter = ParallelBitonicSorter(num_processes=nprocs)
            for size in self._config.sizes:
                arr = self._generate_array(size)
                walls, st, m = self._measure_parallel(sorter, arr)
                run_times[nprocs][size] = walls
                metrics[nprocs][size] = m
                print(
                    f"  Parallel    n={size:>8,}  procs={nprocs}  "
                    f"median={st.median:.4f}s  ±{st.ci_half:.4f}s"
                )
        return run_times, metrics

    def run(self) -> BenchmarkResult:
        runs_per = self._config.warmup_runs + self._config.num_runs
        print("=" * 60)
        print("Bitonic Sort Benchmark")
        print(f"Sizes:          {[f'{s:,}' for s in self._config.sizes]}")
        print(f"Process counts: {self._config.process_counts}")
        print(
            f"Runs per config: {runs_per}"
            f" ({self._config.warmup_runs} warmup + {self._config.num_runs} timed)"
        )
        if self._config.drop_outliers:
            print("Outlier removal: IQR (1.5×) before computing stats")
        print("=" * 60)

        print("\n[1/2] Benchmarking sequential sort...")
        seq_run_times, seq_metrics = self._bench_sequential()

        print("\n[2/2] Benchmarking parallel sort...")
        par_run_times, par_metrics = self._bench_parallel()

        result = BenchmarkResult(
            sequential_run_times=seq_run_times,
            parallel_run_times=par_run_times,
            sequential_metrics=seq_metrics,
            parallel_metrics=par_metrics,
            results_dir=self._config.results_dir,
        )

        print("\nComputing speedup & efficiency...")
        result.compute_metrics()
        for nprocs in sorted(result.speedup.keys()):
            for size in sorted(result.speedup[nprocs].keys()):
                sp = result.speedup[nprocs][size]
                eff = result.efficiency[nprocs][size]
                print(
                    f"  procs={nprocs}  n={size:>8,}"
                    f"  speedup={sp:.3f}x  efficiency={eff:.3f}"
                )

        print("\nSummary table:")
        print_table(result)

        print("\nGenerating plots & saving data...")
        PlotGenerator(result, formats=self._config.plot_formats).generate_all()
        save_csv(result)
        save_latex_table(result)
        save_json(result)

        print("\nDone!")
        return result

```

## В.10. Точка входу (`__main__.py`)

```python
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from benchmark.config import BenchmarkConfig, parse_processes, parse_sizes
from benchmark.runner import BenchmarkRunner


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Bitonic Sort benchmarks (sequential and parallel)."
    )
    parser.add_argument(
        "--sizes",
        type=str,
        default=None,
        metavar="SPEC",
        help="Sizes: comma list or range 10:20 for 2^10..2^20 (default: 10:19)",
    )
    parser.add_argument(
        "--processes",
        type=str,
        default=None,
        metavar="LIST",
        help="Process counts, comma-separated (e.g. 2,4,8) (default: 2,4,8)",
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=None,
        metavar="N",
        help="Number of timed runs per config (default: 5, or BENCH_NUM_RUNS env)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=None,
        metavar="N",
        help="Number of warmup runs per config (default: 2, or BENCH_WARMUP_RUNS env)",
    )
    parser.add_argument(
        "--drop-outliers",
        action="store_true",
        help="Remove outliers with IQR (1.5×) before computing median and CI",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        metavar="FMT",
        help="Plot output format(s), comma-separated: png, svg, pdf (default: png)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    default = BenchmarkConfig.default()
    num_runs = args.num_runs
    if num_runs is None:
        try:
            num_runs = int(os.environ.get("BENCH_NUM_RUNS", "5"))
        except ValueError:
            num_runs = 5
    warmup = args.warmup
    if warmup is None:
        try:
            warmup = int(os.environ.get("BENCH_WARMUP_RUNS", "2"))
        except ValueError:
            warmup = 2
    sizes = parse_sizes(args.sizes) if args.sizes else default.sizes
    process_counts = (
        parse_processes(args.processes) if args.processes else default.process_counts
    )
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    if not formats:
        formats = ["png"]

    config = BenchmarkConfig(
        sizes=sizes,
        process_counts=process_counts,
        num_runs=num_runs,
        warmup_runs=warmup,
        results_dir=default.results_dir,
        disable_gc=default.disable_gc,
        drop_outliers=args.drop_outliers,
        plot_formats=formats,
    )
    runner = BenchmarkRunner(config=config)
    runner.run()


if __name__ == "__main__":
    main()

```

## В.11. `plots_from_data.py`

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from benchmark.load_result import load_benchmark_result
from benchmark.plots import PlotGenerator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate benchmark plots from saved benchmark_data.json."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to benchmark_data.json or to directory containing it",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        metavar="FMT",
        help="Plot format(s), comma-separated: png, svg, pdf (default: png)",
    )
    args = parser.parse_args()

    path = args.path.resolve()
    data_file = path / "benchmark_data.json" if path.is_dir() else path

    if not data_file.exists():
        print(f"File not found: {data_file}", file=sys.stderr)
        return 1

    result = load_benchmark_result(path)
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    if not formats:
        formats = ["png"]

    print(f"Generating plots into {result.results_dir}...")
    PlotGenerator(result, formats=formats).generate_all()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

## В.12. `recommend.py`

```python
from __future__ import annotations

import json
import sys
from pathlib import Path


def load_result(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def recommend_from_data(data: dict) -> list[tuple[int, int, float, float]]:
    speedup = data.get("speedup") or {}
    efficiency = data.get("efficiency") or {}
    if not speedup:
        return []
    sizes = sorted(
        {int(s) for np_ in speedup for s in speedup[str(np_)]},
        key=int,
    )
    nprocs_list = sorted(int(np_) for np_ in speedup)
    out: list[tuple[int, int, float, float]] = []
    for size in sizes:
        best_p = nprocs_list[0]
        best_sp = 0.0
        for np_ in nprocs_list:
            sp = speedup.get(str(np_), {}).get(str(size), 0.0)
            if sp > best_sp:
                best_sp = sp
                best_p = np_
        eff = efficiency.get(str(best_p), {}).get(str(size), 0.0)
        out.append((size, best_p, best_sp, eff))
    return out


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    default_path = root / "results" / "benchmark_data.json"
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    data = load_result(path)
    rows = recommend_from_data(data)
    if not rows:
        print("No speedup data in JSON.", file=sys.stderr)
        return 1
    print("Recommended process count per size (by best speedup):")
    print(f"{'Size':>12}  {'P':>4}  {'Speedup':>10}  {'Efficiency':>10}")
    print("-" * 42)
    for size, p, sp, eff in rows:
        print(f"{size:>12,}  {p:>4}  {sp:>10.3f}  {eff:>10.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

