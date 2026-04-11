"""
Build publication-style figures from lab6_bench.csv (heatmaps + representative slices).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "variant": r["variant"],
                    "nra": int(r["nra"]),
                    "nca": int(r["nca"]),
                    "ncb": int(r["ncb"]),
                    "procs": int(r["procs"]),
                    "seconds": float(r["seconds"]),
                }
            )
    return rows


def build_grid(
    rows: list[dict[str, object]],
    variant: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (n_values ascending, p_values ascending, Z[p_idx, n_idx]) with NaN for holes."""
    sub = [
        r
        for r in rows
        if str(r["variant"]) == variant
        and int(r["nra"]) == int(r["nca"]) == int(r["ncb"])
    ]
    ns = sorted({int(r["nra"]) for r in sub})
    ps = sorted({int(r["procs"]) for r in sub})
    if not ns or not ps:
        return np.array([]), np.array([]), np.array([]).reshape(0, 0)
    n_idx = {n: i for i, n in enumerate(ns)}
    p_idx = {p: i for i, p in enumerate(ps)}
    z = np.full((len(ps), len(ns)), np.nan, dtype=np.float64)
    for r in sub:
        z[p_idx[int(r["procs"])], n_idx[int(r["nra"])]] = float(r["seconds"])
    return np.array(ns), np.array(ps), z


def edges_from_centers(c: np.ndarray) -> np.ndarray:
    """Piecewise-uniform bin edges for pcolormesh from 1D ascending centers."""
    c = np.asarray(c, dtype=np.float64)
    if c.size == 0:
        return c
    if c.size == 1:
        d = 1.0
        return np.array([c[0] - d / 2, c[0] + d / 2])
    left = c[0] - (c[1] - c[0]) / 2
    mid = (c[:-1] + c[1:]) / 2
    right = c[-1] + (c[-1] - c[-2]) / 2
    return np.concatenate([[left], mid, [right]])


def plot_all(csv_path: Path, out_dir: Path) -> list[Path]:
    try:
        import matplotlib
    except ModuleNotFoundError:
        print("matplotlib is required (uv sync in plots/)", file=sys.stderr)
        raise

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        pass

    rows = load_rows(csv_path)
    if not rows:
        raise ValueError("CSV has no data rows")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    # --- 1) Heatmaps: time (log10) for each variant ---
    fig_h, axes_h = plt.subplots(1, 2, figsize=(12.5, 5.2), constrained_layout=True)
    for ax, variant, title in zip(
        axes_h,
        ("blocking", "nonblocking"),
        ("Blocking (MPI_Send / Recv)", "Non-blocking (Isend / Irecv + Wait)"),
        strict=True,
    ):
        ns, ps, z = build_grid(rows, variant)
        if z.size == 0:
            ax.set_visible(False)
            continue
        ze = edges_from_centers(ns)
        pe = edges_from_centers(ps)
        valid = np.isfinite(z) & (z > 0)
        logz = np.full_like(z, np.nan, dtype=np.float64)
        logz[valid] = np.log10(z[valid])
        pcm = ax.pcolormesh(
            ze,
            pe,
            logz,
            shading="flat",
            cmap="viridis",
        )
        cb = fig_h.colorbar(pcm, ax=ax, shrink=0.85)
        cb.set_label(r"$\log_{10}$(wall time / s)")
        ax.set_xlabel(r"$N$ (square $N \times N$ matrices)")
        ax.set_ylabel("MPI processes (-np)")
        ax.set_title(title)
    fig_h.suptitle(
        "Lab 6 — matrix multiply benchmark (master timed interval)", fontsize=12, y=1.02
    )
    p_heat = out_dir / "lab6_heatmap_time.png"
    fig_h.savefig(p_heat, dpi=160, bbox_inches="tight")
    written.append(p_heat)
    plt.close(fig_h)

    # --- 2) Ratio heatmap: blocking / non-blocking ---
    _, _, zb = build_grid(rows, "blocking")
    _, _, zn = build_grid(rows, "nonblocking")
    if zb.size and zn.size and zb.shape == zn.shape:
        ratio = zb / np.clip(zn, 1e-15, None)
        log2r = np.log2(ratio)
        ns, ps, _ = build_grid(rows, "blocking")
        ze = edges_from_centers(ns)
        pe = edges_from_centers(ps)
        fig_r, ax_r = plt.subplots(figsize=(6.8, 5.0), constrained_layout=True)
        vmax = float(np.nanmax(np.abs(log2r)))
        if not np.isfinite(vmax):
            vmax = 0.05
        else:
            vmax = max(vmax, 0.05)
        pcm = ax_r.pcolormesh(
            ze,
            pe,
            log2r,
            shading="flat",
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
        )
        cb = fig_r.colorbar(pcm, ax=ax_r, shrink=0.85)
        cb.set_label("log2(T_blocking / T_nonblocking)")
        ax_r.set_xlabel(r"$N$")
        ax_r.set_ylabel("MPI processes (-np)")
        ax_r.set_title("Relative speed: blocking vs non-blocking")
        p_ratio = out_dir / "lab6_heatmap_ratio.png"
        fig_r.savefig(p_ratio, dpi=160, bbox_inches="tight")
        written.append(p_ratio)
        plt.close(fig_r)

    # --- 3) Slices: time vs N for selected P ---
    pick_p = [2, 4, 8]
    fig_n, axes_n = plt.subplots(
        1, 2, figsize=(11.5, 4.2), sharey=True, constrained_layout=True
    )
    cmap = plt.get_cmap("tab10")
    for ax, variant, title in zip(
        axes_n,
        ("blocking", "nonblocking"),
        ("Blocking", "Non-blocking"),
        strict=True,
    ):
        for k, p in enumerate(pick_p):
            pts = sorted(
                (int(r["nra"]), float(r["seconds"]))
                for r in rows
                if str(r["variant"]) == variant
                and int(r["procs"]) == p
                and int(r["nra"]) == int(r["nca"]) == int(r["ncb"])
            )
            if not pts:
                continue
            xs, ys = zip(*pts)
            ax.plot(
                xs,
                ys,
                "o-",
                color=cmap(k % 10),
                label=f"$P={p}$",
                markersize=3,
                linewidth=1.2,
            )
        ax.set_xlabel(r"$N$")
        ax.set_title(title)
        ax.legend(title="Processes", fontsize=8)
        ax.grid(True, alpha=0.35)
    axes_n[0].set_ylabel("Wall time (s)")
    fig_n.suptitle("Time vs matrix size (selected process counts)", fontsize=11, y=1.03)
    p_n = out_dir / "lab6_slice_time_vs_n.png"
    fig_n.savefig(p_n, dpi=160, bbox_inches="tight")
    written.append(p_n)
    plt.close(fig_n)

    # --- 4) Slices: time vs P for selected N ---
    all_n = sorted(
        {int(r["nra"]) for r in rows if int(r["nra"]) == int(r["nca"]) == int(r["ncb"])}
    )
    pick_n = [all_n[0], all_n[len(all_n) // 2], all_n[-1]] if len(all_n) >= 3 else all_n

    fig_p, axes_p = plt.subplots(
        1, 2, figsize=(11.5, 4.2), sharey=True, constrained_layout=True
    )
    for ax, variant, title in zip(
        axes_p,
        ("blocking", "nonblocking"),
        ("Blocking", "Non-blocking"),
        strict=True,
    ):
        for k, n in enumerate(pick_n):
            pts = sorted(
                (int(r["procs"]), float(r["seconds"]))
                for r in rows
                if str(r["variant"]) == variant and int(r["nra"]) == n
            )
            if not pts:
                continue
            xs, ys = zip(*pts)
            ax.plot(
                xs,
                ys,
                "s-",
                color=cmap(k % 10),
                label=f"$N={n}$",
                markersize=3,
                linewidth=1.2,
            )
        ax.set_xlabel("MPI processes (-np)")
        ax.set_title(title)
        ax.legend(title="Matrix size", fontsize=8)
        ax.grid(True, alpha=0.35)
    axes_p[0].set_ylabel("Wall time (s)")
    fig_p.suptitle("Time vs process count (selected $N$)", fontsize=11, y=1.03)
    p_p = out_dir / "lab6_slice_time_vs_procs.png"
    fig_p.savefig(p_p, dpi=160, bbox_inches="tight")
    written.append(p_p)
    plt.close(fig_p)

    return written


def main() -> int:
    root = project_root()
    ap = argparse.ArgumentParser(description="Plot lab6_bench.csv → PNG figures")
    ap.add_argument(
        "--csv",
        default=None,
        help="input CSV (default: <project>/results/lab6_bench.csv)",
    )
    ap.add_argument(
        "--out-dir", default=None, help="output directory (default: <project>/results)"
    )
    args = ap.parse_args()

    csv_path = Path(args.csv) if args.csv else root / "results" / "lab6_bench.csv"
    if not csv_path.is_file():
        print(f"Missing {csv_path}; run: just task4-bench", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else root / "results"

    try:
        paths = plot_all(csv_path, out_dir)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    for p in paths:
        print(p.resolve())
    return 0


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
