"""Data models for benchmark results and system metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.stats import RunStats, compute_stats


@dataclass
class SystemMetrics:
    """System metrics for one benchmark run (Unix only)."""

    wall_s: float
    cpu_self_s: float
    cpu_children_s: float  # 0 for sequential
    rss_mb: float
    ctx_voluntary: int
    ctx_involuntary: int

    def cpu_utilization(self, nprocs: int) -> float:
        """Child CPU / (wall * nprocs); ideal is ≤1 for good scaling."""
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
    """Timing (run lists + stats), system metrics, speedup and efficiency."""

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
        """Derive median times and RunStats from run-time lists."""
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
        """Derive times/stats from run lists (if present), then speedup and eff."""
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
