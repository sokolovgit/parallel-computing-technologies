"""Benchmark configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def parse_sizes(spec: str) -> list[int]:
    """Parse sizes from CLI: comma-separated list or 'lo:hi' for 2^lo..2^hi."""
    spec = spec.strip()
    if ":" in spec:
        lo_str, hi_str = spec.split(":", 1)
        lo = int(lo_str.strip())
        hi = int(hi_str.strip())
        return [2**k for k in range(lo, hi + 1)]
    return [int(x.strip()) for x in spec.split(",") if x.strip()]


def parse_processes(spec: str) -> list[int]:
    """Parse process counts from CLI: comma-separated list, e.g. '2,4,8'."""
    return [int(x.strip()) for x in spec.split(",") if x.strip()]


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for a benchmark run."""

    sizes: list[int]
    process_counts: list[int]
    num_runs: int
    warmup_runs: int
    results_dir: Path
    disable_gc: bool
    run_baseline: bool
    run_weak_scaling: bool
    weak_scaling_base: int
    drop_outliers: bool
    plot_formats: list[str]

    @classmethod
    def default(cls, results_dir: Path | None = None) -> BenchmarkConfig:
        """Default config: sizes 2^10..2^19, processes 2,4,8."""
        base = Path(__file__).resolve().parent.parent / "results"
        return cls(
            sizes=[2**k for k in range(10, 20)],
            process_counts=[2, 4, 8],
            num_runs=5,
            warmup_runs=2,
            results_dir=results_dir or base,
            disable_gc=True,
            run_baseline=False,
            run_weak_scaling=False,
            weak_scaling_base=2**14,
            drop_outliers=False,
            plot_formats=["png"],
        )
