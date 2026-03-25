from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _float(row: dict, key: str) -> float:
    return float(row[key])


def _int(row: dict, key: str) -> int:
    return int(row[key])


def pick_common_ref_thread(rows: list[dict]) -> int | None:
    """Largest thread count present for both striped and Fox (for fair comparison)."""
    ts = {_int(r, "threads") for r in rows if r["algorithm"] == "striped"}
    tf = {_int(r, "threads") for r in rows if r["algorithm"] == "fox"}
    common = ts & tf
    if common:
        return max(common)
    union = ts | tf
    return max(union) if union else None


def plot_comparison_sequential_striped_fox(rows: list[dict], out_dir: Path, _dev: bool) -> None:
    """1) Sequential vs striped vs Fox — median parallel time vs n (Fox/striped at common max thread count)."""
    seq_by_n: dict[int, float] = {}
    for r in rows:
        if r["algorithm"] == "sequential":
            seq_by_n[_int(r, "n")] = _float(r, "t_parallel_ms")

    ref_t = pick_common_ref_thread(rows)
    if ref_t is None:
        ref_t = 16

    st_by_n: dict[int, float] = {}
    for r in rows:
        if r["algorithm"] == "striped" and _int(r, "threads") == ref_t:
            st_by_n[_int(r, "n")] = _float(r, "t_parallel_ms")

    fox_by_n: dict[int, float] = {}
    for r in rows:
        if r["algorithm"] == "fox" and _int(r, "threads") == ref_t:
            fox_by_n[_int(r, "n")] = _float(r, "t_parallel_ms")

    fig, ax = plt.subplots(figsize=(9, 5))
    markers = ["o", "s", "^"]
    series: list[tuple[str, dict[int, float], str]] = []
    if seq_by_n:
        series.append(("Послідовний", seq_by_n, markers[0]))
    if st_by_n:
        series.append((f"Смугастий (striped), {ref_t} потоків", st_by_n, markers[len(series) % len(markers)]))
    if fox_by_n:
        series.append((f"Фокс (Fox), {ref_t} потоків", fox_by_n, markers[len(series) % len(markers)]))

    for label, data, m in series:
        pts = sorted(data.items(), key=lambda p: p[0])
        ax.plot([p[0] for p in pts], [p[1] for p in pts], marker=m, linestyle="-", label=label)

    ax.set_xlabel("Розмір матриці n")
    ax.set_ylabel("Час (мс, медіана)")
    ax.set_title("Порівняння: послідовний, смугастий і Фокс")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "01_comparison_sequential_striped_fox.png", dpi=150)
    plt.close(fig)


def plot_striped_threads(rows: list[dict], out_dir: Path, _dev: bool) -> None:
    """2) Striped — speedup vs n for each thread count."""
    sub = [r for r in rows if r["algorithm"] == "striped"]
    if not sub:
        return
    by_t: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in sub:
        by_t[_int(r, "threads")].append((_int(r, "n"), _float(r, "speedup")))

    fig, ax = plt.subplots(figsize=(9, 5))
    markers = ["o", "s", "^", "D", "v", "P"]
    for i, t in enumerate(sorted(by_t.keys())):
        pts = sorted(by_t[t], key=lambda p: p[0])
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            marker=markers[i % len(markers)],
            linestyle="-",
            label=f"потоків = {t}",
        )
    ax.set_xlabel("Розмір матриці n")
    ax.set_ylabel("Прискорення (t_послід / t_парал)")
    ax.set_title("Смугастий алгоритм: прискорення vs n для різної кількості потоків")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "02_striped_threads.png", dpi=150)
    plt.close(fig)


def plot_fox_threads(rows: list[dict], out_dir: Path, _dev: bool) -> None:
    """3) Fox — speedup vs n for each thread count."""
    sub = [r for r in rows if r["algorithm"] == "fox"]
    if not sub:
        return
    by_t: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for r in sub:
        by_t[_int(r, "threads")].append((_int(r, "n"), _float(r, "speedup")))

    fig, ax = plt.subplots(figsize=(9, 5))
    markers = ["o", "s", "^", "D", "v", "P"]
    for i, t in enumerate(sorted(by_t.keys())):
        pts = sorted(by_t[t], key=lambda p: p[0])
        ax.plot(
            [p[0] for p in pts],
            [p[1] for p in pts],
            marker=markers[i % len(markers)],
            linestyle="-",
            label=f"потоків = {t} (q = {int(math.sqrt(t))})",
        )
    ax.set_xlabel("Розмір матриці n")
    ax.set_ylabel("Прискорення (t_послід / t_парал)")
    ax.set_title("Фокс: прискорення vs n для різної кількості потоків (q×q сітка)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "03_fox_threads.png", dpi=150)
    plt.close(fig)


def plot_fox_vs_striped(rows: list[dict], out_dir: Path, _dev: bool) -> None:
    """4) Fox vs striped — parallel time vs n at the same thread counts."""
    ts = {_int(r, "threads") for r in rows if r["algorithm"] == "striped"}
    tf = {_int(r, "threads") for r in rows if r["algorithm"] == "fox"}
    common = sorted(ts & tf)
    if not common:
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    markers_s = ["o", "v", "s", "^"]
    markers_f = ["D", "p", "P", "X"]
    for i, t in enumerate(common):
        st = {
            _int(r, "n"): _float(r, "t_parallel_ms")
            for r in rows
            if r["algorithm"] == "striped" and _int(r, "threads") == t
        }
        fx = {
            _int(r, "n"): _float(r, "t_parallel_ms")
            for r in rows
            if r["algorithm"] == "fox" and _int(r, "threads") == t
        }
        if st:
            pts = sorted(st.items(), key=lambda p: p[0])
            ax.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                marker=markers_s[i % len(markers_s)],
                linestyle="-",
                label=f"striped, {t} потоків",
            )
        if fx:
            pts = sorted(fx.items(), key=lambda p: p[0])
            ax.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                marker=markers_f[i % len(markers_f)],
                linestyle="--",
                label=f"Fox, {t} потоків",
            )

    ax.set_xlabel("Розмір матриці n")
    ax.set_ylabel("Час паралельної фази (мс, медіана)")
    ax.set_title("Фокс vs смугастий: час при однакових кількостях потоків")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(out_dir / "04_fox_vs_striped.png", dpi=150)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Графіки з CSV бенчмарку (лаб. матричне множення)")
    p.add_argument("--input", "-i", type=Path, required=True, help="CSV з Java harness")
    p.add_argument("--out", "-o", type=Path, required=True, help="Каталог для PNG")
    p.add_argument("--dev", action="store_true", help="Швидкий прев'ю-режим")
    args = p.parse_args()

    rows = load_rows(args.input)
    if not rows:
        raise SystemExit("No rows in input")

    os.makedirs(args.out, exist_ok=True)
    plot_comparison_sequential_striped_fox(rows, args.out, args.dev)
    plot_striped_threads(rows, args.out, args.dev)
    plot_fox_threads(rows, args.out, args.dev)
    plot_fox_vs_striped(rows, args.out, args.dev)
    print(f"Wrote figures to {args.out.resolve()}")


if __name__ == "__main__":
    main()
