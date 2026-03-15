"""Load BenchmarkResult from saved benchmark_data.json."""

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
    """
    Load benchmark data from JSON and return a BenchmarkResult.

    path: path to benchmark_data.json or to a directory containing it.
    """
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
