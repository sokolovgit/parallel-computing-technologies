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
