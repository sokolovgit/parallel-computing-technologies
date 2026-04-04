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


def _task_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [r for r in rows if r.get("task") == "task1"]


def plot_speedup_vs_parallelism(rows: list[dict[str, str]], out_dir: Path) -> None:
    """Криві S(P) для кожного порогу рядків."""
    by_t: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in _task_rows(rows):
        by_t[_i(r, "line_threshold")].append((_i(r, "parallelism"), _f(r, "speedup")))

    fig, ax = plt.subplots(figsize=(12, 6.5))
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "h", "8", "p", "*"]
    for i, t in enumerate(sorted(by_t.keys())):
        pts = sorted(by_t[t], key=lambda p: p[0])
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            marker=markers[i % len(markers)],
            linestyle="-",
            markersize=4,
            label=f"T={t}",
        )
    ax.set_xlabel("Паралелізм P (ForkJoinPool)")
    ax.set_ylabel("Прискорення S = t_seq / t_par")
    ax.set_title("Завдання 1: прискорення vs паралелізм")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2, loc="best", framealpha=0.92)
    fig.tight_layout()
    fig.savefig(out_dir / "01_task1_speedup_vs_parallelism.png", dpi=160)
    plt.close(fig)


def plot_efficiency_vs_parallelism(rows: list[dict[str, str]], out_dir: Path) -> None:
    """E = S / P для кожного порогу."""
    by_t: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in _task_rows(rows):
        by_t[_i(r, "line_threshold")].append((_i(r, "parallelism"), _f(r, "efficiency")))

    fig, ax = plt.subplots(figsize=(12, 6.5))
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "h", "8", "p", "*"]
    for i, t in enumerate(sorted(by_t.keys())):
        pts = sorted(by_t[t], key=lambda p: p[0])
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            marker=markers[i % len(markers)],
            linestyle="-",
            markersize=4,
            label=f"T={t}",
        )
    ax.set_xlabel("Паралелізм P")
    ax.set_ylabel("Ефективність E = S / P")
    ax.set_title("Завдання 1: ефективність vs паралелізм")
    ax.set_ylim(bottom=0.0)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2, loc="best", framealpha=0.92)
    fig.tight_layout()
    fig.savefig(out_dir / "02_task1_efficiency_vs_parallelism.png", dpi=160)
    plt.close(fig)


def plot_speedup_vs_threshold(rows: list[dict[str, str]], out_dir: Path) -> None:
    """Криві S(T) для кожного P — додаткова вісь «розмірність» порогу."""
    by_p: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in _task_rows(rows):
        by_p[_i(r, "parallelism")].append((_i(r, "line_threshold"), _f(r, "speedup")))

    fig, ax = plt.subplots(figsize=(12, 6.5))
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "h", "8"]
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
    ax.set_xlabel("Поріг рядків T (листові задачі)")
    ax.set_ylabel("Прискорення S")
    ax.set_title("Завдання 1: прискорення vs поріг рядків")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2, loc="best", framealpha=0.92)
    fig.tight_layout()
    fig.savefig(out_dir / "03_task1_speedup_vs_threshold.png", dpi=160)
    plt.close(fig)


def plot_times_vs_parallelism(rows: list[dict[str, str]], out_dir: Path) -> None:
    """Час seq/par vs P при найменшому T (найбільше точок на осі P)."""
    task_rows = _task_rows(rows)
    if not task_rows:
        return
    min_t = min(_i(r, "line_threshold") for r in task_rows)
    sub = [r for r in task_rows if _i(r, "line_threshold") == min_t]
    by_p: dict[int, tuple[float, float]] = {}
    for r in sub:
        p = _i(r, "parallelism")
        by_p[p] = (_f(r, "t_seq_ms"), _f(r, "t_par_ms"))

    fig, ax = plt.subplots(figsize=(12, 6))
    pts = sorted(by_p.items(), key=lambda x: x[0])
    xs = [p for p, _ in pts]
    seq_y = [t[0] for _, t in pts]
    par_y = [t[1] for _, t in pts]
    ax.plot(xs, seq_y, marker="o", linestyle="-", markersize=5, label="Послідовно")
    ax.plot(xs, par_y, marker="s", linestyle="-", markersize=5, label="ForkJoin")
    ax.set_xlabel("Паралелізм P")
    ax.set_ylabel("Середній час (мс)")
    ax.set_title(f"Завдання 1: час vs P (мінімальний поріг T = {min_t})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "04_task1_times_vs_parallelism.png", dpi=160)
    plt.close(fig)


def plot_speedup_heatmap(rows: list[dict[str, str]], out_dir: Path) -> None:
    """Теплова карта S(P, line_threshold)."""
    task_rows = _task_rows(rows)
    if not task_rows:
        return
    ps = sorted({_i(r, "parallelism") for r in task_rows})
    ts = sorted({_i(r, "line_threshold") for r in task_rows})
    grid = [[0.0 for _ in ps] for _ in ts]
    idx_p = {p: i for i, p in enumerate(ps)}
    idx_t = {t: i for i, t in enumerate(ts)}
    for r in task_rows:
        grid[idx_t[_i(r, "line_threshold")]][idx_p[_i(r, "parallelism")]] = _f(r, "speedup")

    fig_h = max(6.0, 0.45 * len(ts) + 2.0)
    fig_w = max(10.0, 0.55 * len(ps) + 3.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xticks(range(len(ps)), labels=[str(p) for p in ps])
    ax.set_yticks(range(len(ts)), labels=[str(t) for t in ts])
    ax.set_xlabel("Паралелізм P")
    ax.set_ylabel("Поріг рядків T")
    ax.set_title("Завдання 1: прискорення (теплова карта)")
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right")
    fig.colorbar(im, ax=ax, label="S")
    fig.tight_layout()
    fig.savefig(out_dir / "05_task1_speedup_heatmap.png", dpi=160)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Графіки з CSV бенчмарку lab4 (task1)")
    p.add_argument("--input", "-i", type=Path, required=True)
    p.add_argument("--out", "-o", type=Path, required=True)
    p.add_argument("--dev", action="store_true")
    args = p.parse_args()

    rows = load_rows(args.input)
    if not rows:
        raise SystemExit("No rows in input")

    os.makedirs(args.out, exist_ok=True)
    plot_speedup_vs_parallelism(rows, args.out)
    plot_efficiency_vs_parallelism(rows, args.out)
    plot_speedup_vs_threshold(rows, args.out)
    plot_times_vs_parallelism(rows, args.out)
    plot_speedup_heatmap(rows, args.out)
    print(f"Wrote figures to {args.out.resolve()}")


if __name__ == "__main__":
    main()
