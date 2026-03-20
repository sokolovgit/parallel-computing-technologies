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
