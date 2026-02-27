"""Entry point for running the benchmark as a module: python -m benchmark."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure src (bitonic package) is on path when running as __main__
_root = Path(__file__).resolve().parent.parent
_src = _root / "src"
if _src.exists() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from benchmark.runner import BenchmarkRunner


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Bitonic Sort benchmarks (sequential and parallel)."
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
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Also run np.sort baseline comparison",
    )
    parser.add_argument(
        "--weak-scaling",
        action="store_true",
        help="Also run weak scaling benchmarks",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
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
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    if not formats:
        formats = ["png"]

    runner = BenchmarkRunner(
        num_runs=10,
        warmup_runs=warmup,
        drop_outliers=True,
        run_baseline=args.baseline,
        run_weak_scaling=args.weak_scaling,
        plot_formats=formats,
    )
    runner.run()


if __name__ == "__main__":
    main()
