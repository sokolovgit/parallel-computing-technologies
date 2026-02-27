"""Export benchmark results to CSV, JSON, LaTeX and console."""

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

# Must match bitonic.parallel._MIN_COMPARISONS_PER_WORKER for fallback detection
_MIN_COMPARISONS_PER_WORKER = 50_000


def _next_power_of_two(n: int) -> int:
    if n <= 0:
        return 1
    p = 1
    while p < n:
        p <<= 1
    return p


def _used_parallel_fallback(nprocs: int, size: int) -> bool:
    """True if parallel sorter uses sequential fallback for this (nprocs, size)."""
    if nprocs <= 1:
        return False
    padded_n = _next_power_of_two(size)
    cmp_per_worker = (padded_n // 2) // nprocs
    return cmp_per_worker < _MIN_COMPARISONS_PER_WORKER


def _metadata() -> dict[str, Any]:
    """Environment metadata for reproducibility."""
    return {
        "python_version": sys.version.split()[0],
        "cpu_count": mp.cpu_count(),
        "platform": platform.platform(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def print_table(result: BenchmarkResult) -> None:
    """Print main results as a formatted table."""
    sizes = sorted(result.sequential_times.keys())
    nprocs_list = sorted(result.parallel_times.keys())
    col_w = 14

    # Iterative table
    header = f"{'Size':>{col_w}}" + f"{'Seq(iter)':>{col_w}}"
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


def print_system_metrics(result: BenchmarkResult) -> None:
    """Print system metrics for a few representative sizes."""
    if not HAS_RESOURCE:
        print("  (System metrics: unavailable on this platform)")
        return
    sizes = sorted(result.sequential_times.keys())
    if not sizes:
        return
    idx = [0, len(sizes) // 2, -1]
    for i in idx:
        size = sizes[i]
        print(f"\n  --- n = {size:,} ---")
        sm = result.sequential_metrics.get(size)
        if sm:
            print(
                f"    Sequential: wall={sm.wall_s:.4f}s"
                f" cpu_self={sm.cpu_self_s:.4f}s rss={sm.rss_mb:.2f}MB"
                f" ctx_vol={sm.ctx_voluntary} ctx_inv={sm.ctx_involuntary}"
            )
        for nprocs in sorted(result.parallel_metrics.keys()):
            pm = result.parallel_metrics.get(nprocs, {}).get(size)
            if pm:
                util = pm.cpu_utilization(nprocs)
                print(
                    f"    Parallel P={nprocs}: wall={pm.wall_s:.4f}s"
                    f" cpu_children={pm.cpu_children_s:.4f}s util={util:.2%}"
                    f" rss={pm.rss_mb:.2f}MB ctx_inv={pm.ctx_involuntary}"
                )


def print_bottleneck_analysis(result: BenchmarkResult) -> None:
    """Interpret metrics and suggest bottlenecks / improvements."""
    print("\n  --- Bottleneck analysis ---")
    if not HAS_RESOURCE or not result.parallel_metrics:
        print(
            "  (No system metrics; run on Unix for CPU/memory/context-switch analysis)"
        )
        return
    sizes = sorted(result.sequential_times.keys())
    nprocs_list = sorted(result.parallel_metrics.keys())
    if not sizes or not nprocs_list:
        return
    fallback_pairs = [
        (nprocs, size)
        for nprocs in nprocs_list
        for size in sizes
        if _used_parallel_fallback(nprocs, size)
    ]
    low_util_sizes: list[int] = []
    high_ctx_sizes: list[int] = []
    for size in sizes:
        for nprocs in nprocs_list:
            pm = result.parallel_metrics.get(nprocs, {}).get(size)
            if not pm:
                continue
            util = pm.cpu_utilization(nprocs)
            if util < 0.5 and size not in low_util_sizes:
                low_util_sizes.append(size)
            if pm.ctx_involuntary > 1000 and size not in high_ctx_sizes:
                high_ctx_sizes.append(size)
    observations: list[str] = []
    if fallback_pairs:
        pairs_str = ", ".join(
            f"P={p} n={n:,}" for (p, n) in sorted(fallback_pairs)[:12]
        )
        if len(fallback_pairs) > 12:
            pairs_str += f" (+{len(fallback_pairs) - 12} more)"
        observations.append(
            f"Sequential fallback used (work per worker < {_MIN_COMPARISONS_PER_WORKER:,}): {pairs_str}. "
            "Reported 'parallel' time is single-process; use larger n for true parallel."
        )
    if low_util_sizes:
        observations.append(
            "Low CPU utilization at small n: parallel path may use sequential "
            "fallback when work per worker is below threshold; otherwise pool "
            "creation + barriers dominate. Use larger n for meaningful speedup."
        )
    eff_best = 0.0
    for nprocs in nprocs_list:
        for size in sizes:
            e = result.efficiency.get(nprocs, {}).get(size, 0)
            eff_best = max(eff_best, e)
    if eff_best < 0.5:
        observations.append(
            "Efficiency below 50%: memory bandwidth or barrier overhead may "
            "dominate. Parallel implementation uses one barrier per size (not "
            "per stride) to limit IPC; ensure n is large enough for your P."
        )
    elif eff_best < 0.8:
        observations.append(
            "Moderate efficiency: bitonic sort is memory-bound at large n; "
            "speedup is limited by cache/memory bus. Expect 60–70% at best."
        )
    if high_ctx_sizes:
        observations.append(
            "High involuntary context switches in some runs: possible "
            "memory pressure or scheduler contention. Larger per-worker work "
            "chunks may reduce switching."
        )
    if not observations:
        observations.append("No strong bottleneck signals from current metrics.")
    for i, obs in enumerate(observations, 1):
        print(f"  {i}. {obs}")


def save_csv(result: BenchmarkResult) -> None:
    """Write main results table to CSV."""
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
    """Export a summary table as LaTeX for the report."""
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


def save_json(result: BenchmarkResult) -> None:
    """Write full benchmark data and metadata to JSON."""
    data: dict[str, Any] = {
        "metadata": _metadata(),
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
        "speedup": {
            str(np_): {str(s): round(sp, 4) for s, sp in smap.items()}
            for np_, smap in result.speedup.items()
        },
        "efficiency": {
            str(np_): {str(s): round(e, 4) for s, e in emap.items()}
            for np_, emap in result.efficiency.items()
        },
    }
    if result.sequential_run_times:
        data["sequential_run_times"] = {
            str(k): v for k, v in result.sequential_run_times.items()
        }
    if result.parallel_run_times:
        data["parallel_run_times"] = {
            str(np_): {str(s): t for s, t in st.items()}
            for np_, st in result.parallel_run_times.items()
        }
    if HAS_RESOURCE and result.sequential_metrics:
        data["sequential_metrics"] = {
            str(s): (m.to_dict() if m else None)
            for s, m in result.sequential_metrics.items()
        }
    if HAS_RESOURCE and result.parallel_metrics:
        data["parallel_metrics"] = {
            str(np_): {str(s): (m.to_dict() if m else None) for s, m in smap.items()}
            for np_, smap in result.parallel_metrics.items()
        }
    data["cpu_utilization"] = {}
    for np_ in result.parallel_metrics:
        data["cpu_utilization"][str(np_)] = {}
        for s, m in result.parallel_metrics[np_].items():
            data["cpu_utilization"][str(np_)][str(s)] = (
                round(m.cpu_utilization(np_), 4) if m else None
            )
    if result.baseline_times:
        data["baseline_times"] = {str(k): v for k, v in result.baseline_times.items()}
        data["baseline_stats"] = {
            str(k): {"median": v.median, "ci_half": v.ci_half}
            for k, v in result.baseline_stats.items()
        }
    if result.weak_scaling_parallel_times:
        data["weak_scaling_sequential_times"] = {
            str(k): v for k, v in result.weak_scaling_sequential_times.items()
        }
        data["weak_scaling_parallel_times"] = {
            str(k): v for k, v in result.weak_scaling_parallel_times.items()
        }
    path = result.results_dir / "benchmark_data.json"
    path.write_text(json.dumps(data, indent=2))
    print(f"  Saved {path}")
