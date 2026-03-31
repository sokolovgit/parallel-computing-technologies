#!/usr/bin/env python3
"""
Build a hierarchical Excel table from benchmark CSV (BenchmarkRunner export).

Column layout (3-level MultiIndex):
  Sequential Algorithm | (empty) | Time, s
  Striped Algorithm   | 4/9/25 threads | Time, s | Speedup
  Fox Algorithm       | 4/9/25 threads | Time, s | Speedup

Times are converted from t_parallel_ms / t_sequential_ms to seconds.

Usage:
  just hierarchical-table ../docs/results/latest.csv results/matrix_table.xlsx   # from lab3/project

  cd scripts && uv sync && uv run python csv_to_hierarchical_table.py ../../docs/results/latest.csv -o ../results/matrix_table.xlsx

  # or: pip install -r requirements.txt
  python csv_to_hierarchical_table.py path/to/latest.csv -o out.xlsx
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

ALGO_LABELS = {
    "striped": "Striped Algorithm",
    "fox": "Fox Algorithm",
}

PARALLEL_ORDER = ["striped", "fox"]


def load_benchmark_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "algorithm",
        "n",
        "threads",
        "t_parallel_ms",
        "t_sequential_ms",
        "speedup",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")
    return df


def build_hierarchical_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame indexed by n with MultiIndex columns."""
    seq = (
        df.loc[df["algorithm"] == "sequential", ["n", "t_sequential_ms"]]
        .drop_duplicates(subset=["n"])
        .set_index("n")["t_sequential_ms"]
        / 1000.0
    )
    seq.name = ("Sequential Algorithm", "", "Time, s")

    par = df.loc[df["algorithm"].isin(PARALLEL_ORDER)].copy()
    par = par.sort_values(["n", "algorithm", "threads"])
    par = par.drop_duplicates(subset=["n", "algorithm", "threads"], keep="last")

    all_n = sorted(df["n"].unique())

    columns: dict[tuple[str, str, str], pd.Series] = {}
    columns[("Sequential Algorithm", "", "Time, s")] = seq.reindex(all_n)

    for algo in PARALLEL_ORDER:
        label = ALGO_LABELS[algo]
        sub = par.loc[par["algorithm"] == algo]
        for t in sorted(sub["threads"].unique()):
            block = sub.loc[sub["threads"] == t].set_index("n")
            time_s = block["t_parallel_ms"] / 1000.0
            speedup = block["speedup"]
            columns[(label, f"{int(t)} threads", "Time, s")] = time_s.reindex(all_n)
            columns[(label, f"{int(t)} threads", "Speedup")] = speedup.reindex(all_n)

    out = pd.DataFrame(columns)
    out.index.name = "Matrix Size"
    out = out.sort_index()
    return out


def _resolve_path(p: Path, base: Path | None) -> Path:
    """Resolve relative paths against base (lab3/project when set); keep absolute paths."""
    p = p.expanduser()
    if p.is_absolute():
        return p.resolve()
    if base is not None:
        return (base / p).resolve()
    return p.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export benchmark CSV to hierarchical Excel table."
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to benchmark CSV (e.g. results/latest.csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("matrix_table.xlsx"),
        help="Output .xlsx path (default: matrix_table.xlsx)",
    )
    args = parser.parse_args()

    base_env = os.environ.get("MATMUL_HOME", "").strip()
    base = Path(base_env).resolve() if base_env else None

    csv_path = _resolve_path(args.csv_path, base)
    out_path = _resolve_path(args.output, base)

    df = load_benchmark_csv(csv_path)
    table = build_hierarchical_frame(df)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Results", merge_cells=True)

    print(f"Wrote {out_path} ({len(table)} rows, {len(table.columns)} columns)")


if __name__ == "__main__":
    main()
