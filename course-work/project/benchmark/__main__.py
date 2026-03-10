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

from benchmark.config import BenchmarkConfig, parse_processes, parse_sizes
from benchmark.runner import BenchmarkRunner


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Bitonic Sort benchmarks (sequential and parallel)."
    )
    parser.add_argument(
        "--sizes",
        type=str,
        default=None,
        metavar="SPEC",
        help="Input sizes: comma-separated (e.g. 1024,8192) or range 10:20 for 2^10..2^20 (default: 10:19)",
    )
    parser.add_argument(
        "--processes",
        type=str,
        default=None,
        metavar="LIST",
        help="Process counts, comma-separated (e.g. 2,4,8) (default: 2,4,8)",
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
    default = BenchmarkConfig.default()
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
    sizes = parse_sizes(args.sizes) if args.sizes else default.sizes
    process_counts = (
        parse_processes(args.processes) if args.processes else default.process_counts
    )
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    if not formats:
        formats = ["png"]

    config = BenchmarkConfig(
        sizes=sizes,
        process_counts=process_counts,
        num_runs=num_runs,
        warmup_runs=warmup,
        results_dir=default.results_dir,
        disable_gc=default.disable_gc,
        run_baseline=args.baseline,
        run_weak_scaling=args.weak_scaling,
        weak_scaling_base=default.weak_scaling_base,
        drop_outliers=args.drop_outliers,
        plot_formats=formats,
    )
    runner = BenchmarkRunner(config=config)
    runner.run()


if __name__ == "__main__":
    main()
