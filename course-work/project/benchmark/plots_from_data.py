from __future__ import annotations

import argparse
import sys
from pathlib import Path

from benchmark.load_result import load_benchmark_result
from benchmark.plots import PlotGenerator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate benchmark plots from saved benchmark_data.json."
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to benchmark_data.json or to directory containing it",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="png",
        metavar="FMT",
        help="Plot format(s), comma-separated: png, svg, pdf (default: png)",
    )
    args = parser.parse_args()

    path = args.path.resolve()
    data_file = path / "benchmark_data.json" if path.is_dir() else path

    if not data_file.exists():
        print(f"File not found: {data_file}", file=sys.stderr)
        return 1

    result = load_benchmark_result(path)
    formats = [f.strip().lower() for f in args.format.split(",") if f.strip()]
    if not formats:
        formats = ["png"]

    print(f"Generating plots into {result.results_dir}...")
    PlotGenerator(result, formats=formats).generate_all()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
