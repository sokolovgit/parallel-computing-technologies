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


def _json_metadata() -> dict[str, Any]:
    """Environment metadata for reproducibility."""
    return {
        "python_version": sys.version.split()[0],
        "cpu_count": mp.cpu_count(),
        "platform": platform.platform(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def save_equipment_file(result: BenchmarkResult) -> None:
    """Write equipment/metadata summary for the report (обладнання)."""
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
    """Print main results as a formatted table."""
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


def _json_sequential(result: BenchmarkResult) -> dict[str, Any]:
    """Sequential times, stats, run_times, and optional metrics."""
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
    """Parallel times, stats, run_times, and optional metrics."""
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
    """Speedup, efficiency, and CPU utilization."""
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
    """Write full benchmark data and metadata to JSON."""
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
