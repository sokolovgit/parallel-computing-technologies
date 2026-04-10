from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib.pyplot as plt


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def aggregate_by_key(
    rows: list[dict[str, str]], key_name: str, metrics: tuple[str, ...]
) -> tuple[list[float], dict[str, tuple[list[float], list[float]]]]:
    """Return sorted x values and for each metric: (mean per x, stdev per x)."""
    buckets: dict[float, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in rows:
        x = _f(r, key_name)
        for m in metrics:
            buckets[x][m].append(_f(r, m))
    xs = sorted(buckets.keys())
    out: dict[str, tuple[list[float], list[float]]] = {m: ([], []) for m in metrics}
    for x in xs:
        for m in metrics:
            vals = buckets[x][m]
            out[m][0].append(mean(vals))
            out[m][1].append(stdev(vals) if len(vals) > 1 else 0.0)
    return xs, out


def plot_load_sweep(rows: list[dict[str, str]], out_dir: Path) -> None:
    if not rows:
        return
    xs, agg = aggregate_by_key(rows, "meanIA_ms", ("meanQueue", "P_reject", "wall_s"))
    mq_m, mq_s = agg["meanQueue"]
    pr_m, pr_s = agg["P_reject"]

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 5))
    ax0.errorbar(xs, mq_m, yerr=mq_s, marker="o", linestyle="-", capsize=3, color="C0")
    ax0.set_xlabel("Середній інтервал надходження (мс)")
    ax0.set_ylabel("Середня довжина черги (середнє по реплікаціях)")
    ax0.set_title("СМО: черга vs інтенсивність надходження\n(N=4, K=8, 20 прогонів/точку)")
    ax0.grid(True, alpha=0.3)

    ax1.errorbar(xs, pr_m, yerr=pr_s, marker="s", linestyle="-", capsize=3, color="C1")
    ax1.set_xlabel("Середній інтервал надходження (мс)")
    ax1.set_ylabel("Ймовірність відмови")
    ax1.set_title("СМО: відмови vs інтенсивність надходження")
    ax1.set_ylim(bottom=0.0)
    ax1.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "01_smo_by_load_meanIA.png", dpi=160)
    plt.close(fig)


def plot_queue_sweep(rows: list[dict[str, str]], out_dir: Path) -> None:
    if not rows:
        return
    xs, agg = aggregate_by_key(rows, "queue", ("meanQueue", "P_reject"))
    mq_m, mq_s = agg["meanQueue"]
    pr_m, pr_s = agg["P_reject"]

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 5))
    ax0.errorbar(xs, mq_m, yerr=mq_s, marker="o", linestyle="-", capsize=3, color="C2")
    ax0.set_xlabel("Місткість черги K")
    ax0.set_ylabel("Середня довжина черги")
    ax0.set_title("СМО: черга vs місткість буфера\n(N=4, meanIA=0.05 мс, 20 прогонів/точку)")
    ax0.grid(True, alpha=0.3)

    ax1.errorbar(xs, pr_m, yerr=pr_s, marker="s", linestyle="-", capsize=3, color="C3")
    ax1.set_xlabel("Місткість черги K")
    ax1.set_ylabel("Ймовірність відмови")
    ax1.set_title("СМО: відмови vs місткість буфера")
    ax1.set_ylim(bottom=0.0)
    ax1.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_dir / "02_smo_by_queue_capacity.png", dpi=160)
    plt.close(fig)


def plot_wall_time_by_load(rows: list[dict[str, str]], out_dir: Path) -> None:
    if not rows:
        return
    xs, agg = aggregate_by_key(rows, "meanIA_ms", ("wall_s",))
    wt_m, wt_s = agg["wall_s"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.errorbar(xs, wt_m, yerr=wt_s, marker="o", linestyle="-", capsize=3, color="C4")
    ax.set_xlabel("Середній інтервал надходження (мс)")
    ax.set_ylabel("Час одного прогону (с, стіна)")
    ax.set_title("Тривалість імітації vs навантаження (minServed=1000)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "03_smo_wall_time_by_load.png", dpi=160)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description="Графіки з CSV бенчмарку lab5 (Task1Benchmark)")
    p.add_argument(
        "--by-load",
        type=Path,
        default=None,
        help="CSV з колонкою meanIA_ms (lab5_by_load.csv)",
    )
    p.add_argument(
        "--by-queue",
        type=Path,
        default=None,
        help="CSV з колонкою queue (lab5_by_queue.csv)",
    )
    p.add_argument("--out", "-o", type=Path, required=True)
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)

    if args.by_load and args.by_load.is_file():
        rows = load_rows(args.by_load)
        plot_load_sweep(rows, args.out)
        plot_wall_time_by_load(rows, args.out)
        print(f"Load sweep figures from {args.by_load}")
    else:
        print("Skip by-load plots (missing file)")

    if args.by_queue and args.by_queue.is_file():
        rows = load_rows(args.by_queue)
        plot_queue_sweep(rows, args.out)
        print(f"Queue sweep figures from {args.by_queue}")
    else:
        print("Skip by-queue plots (missing file)")

    print(f"Wrote figures to {args.out.resolve()}")


if __name__ == "__main__":
    main()
