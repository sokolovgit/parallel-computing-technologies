"""Benchmark sequential vs parallel bitonic sort.

Measures execution time and system metrics (CPU, memory, context switches),
computes speedup and efficiency with 95% CI, and produces plots/tables for reports.
"""

import sys
from pathlib import Path

# Ensure src (bitonic package) is on path for benchmark imports
_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from benchmark.models import BenchmarkResult, SystemMetrics
from benchmark.runner import BenchmarkRunner
from benchmark.stats import RunStats

__all__ = [
    "BenchmarkResult",
    "BenchmarkRunner",
    "RunStats",
    "SystemMetrics",
]
