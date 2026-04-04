"""Графіки для CSV завдання 2 (матриці, ForkJoin). Запуск: python -m lab4_plots.task2 -i ... -o ..."""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def _i(row: dict[str, str], key: str) -> int:
    return int(row[key])


def plot_speedup_vs_n(rows: list[dict[str, str]], out_dir: Path) -> None:
    by_p: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in rows:
        if r.get("task") != "task2":
            continue
        by_p[_i(r, "parallelism")].append((_i(r, "n"), _f(r, "speedup")))

    fig, ax = plt.subplots(figsize=(11, 6))
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "h"]
    for i, p in enumerate(sorted(by_p.keys())):
        pts = sorted(by_p[p], key=lambda x: x[0])
        ax.plot(
            [x[0] for x in pts],
            [x[1] for x in pts],
            marker=markers[i % len(markers)],
            linestyle="-",
            markersize=4,
            label=f"P={p}",
        )
    ax.set_xlabel("Розмір матриці n")
    ax.set_ylabel("Прискорення S")
    ax.set_title("Завдання 2 (стрічкове МН, ForkJoin): прискорення vs n")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2, loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "task2_speedup_vs_n.png", dpi=160)
    plt.close(fig)


def plot_speedup_vs_p(rows: list[dict[str, str]], out_dir: Path) -> None:
    by_n: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in rows:
        if r.get("task") != "task2":
            continue
        by_n[_i(r, "n")].append((_i(r, "parallelism"), _f(r, "speedup")))

    fig, ax = plt.subplots(figsize=(11, 6))
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">"]
    for i, n in enumerate(sorted(by_n.keys())):
        pts = sorted(by_n[n], key=lambda x: x[0])
        ax.plot(
            [x[0] for x in pts],
            [x[1] for x in pts],
            marker=markers[i % len(markers)],
            linestyle="-",
            markersize=4,
            label=f"n={n}",
        )
    ax.set_xlabel("Паралелізм P")
    ax.set_ylabel("Прискорення S")
    ax.set_title("Завдання 2: прискорення vs P")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2, loc="best")
    fig.tight_layout()
    fig.savefig(out_dir / "task2_speedup_vs_p.png", dpi=160)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", type=Path, required=True)
    p.add_argument("--out", "-o", type=Path, required=True)
    args = p.parse_args()
    rows = load_rows(args.input)
    if not rows:
        raise SystemExit("empty csv")
    os.makedirs(args.out, exist_ok=True)
    plot_speedup_vs_n(rows, args.out)
    plot_speedup_vs_p(rows, args.out)
    print(f"Wrote task2 figures to {args.out.resolve()}")


if __name__ == "__main__":
    main()
