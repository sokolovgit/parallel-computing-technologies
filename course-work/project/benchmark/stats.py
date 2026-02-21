"""Statistics and system-metric helpers for benchmarking."""

from __future__ import annotations

import math
import statistics
import sys
from dataclasses import dataclass

# Optional: system metrics (Unix only)
try:
    import resource

    HAS_RESOURCE = hasattr(resource, "getrusage") and sys.platform != "win32"
except ImportError:
    HAS_RESOURCE = False


@dataclass(frozen=True)
class RunStats:
    """Summary statistics for a set of run times (median, 95% CI)."""

    median: float
    mean: float
    stdev: float
    ci_half: float  # half-width of 95% CI

    @property
    def ci_low(self) -> float:
        return max(0.0, self.median - self.ci_half)

    @property
    def ci_high(self) -> float:
        return self.median + self.ci_half


def compute_stats(times: list[float]) -> RunStats:
    """Compute median, mean, stdev, and 95% CI from a list of run times."""
    if not times:
        return RunStats(median=0.0, mean=0.0, stdev=0.0, ci_half=0.0)
    n = len(times)
    median = statistics.median(times)
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if n >= 2 else 0.0
    ci_half = (1.96 * stdev / math.sqrt(n)) if n >= 2 else 0.0
    return RunStats(median=median, mean=mean, stdev=stdev, ci_half=ci_half)


def speedup_ci_half(seq_stats: RunStats, par_stats: RunStats) -> float:
    """Approximate 95% CI half-width for speedup = T_seq / T_par (error propagation)."""
    if par_stats.median <= 0:
        return 0.0
    a = seq_stats.ci_half / par_stats.median
    b = (seq_stats.median * par_stats.ci_half) / (par_stats.median * par_stats.median)
    return math.sqrt(a * a + b * b)


def rss_mb(ru_maxrss: float) -> float:
    """Convert ru_maxrss to MB (Linux: KB, macOS: bytes)."""
    if sys.platform == "darwin":
        return ru_maxrss / (1024 * 1024)
    return ru_maxrss / 1024
