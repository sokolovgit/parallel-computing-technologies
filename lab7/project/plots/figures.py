"""Build publication-style figures from lab7_bench.csv."""

from __future__ import annotations

import csv
from pathlib import Path


def build_grid(
    rows: list[dict[str, object]],
    variant: str,
):
    import numpy as np

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


def edges_from_centers(c):
    import numpy as np

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


def load_csv_rows(path: Path) -> list[dict[str, object]]:
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


def plot_all(
    csv_path: Path,
    out_dir: Path,
    modes: list[str],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        pass

    rows = load_csv_rows(csv_path)
    if not rows:
        raise ValueError("CSV has no data rows")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    labels = {
        "p2p": "P2P (Send / Recv)",
        "collective_sbg": "Scatterv + Bcast + Gatherv",
        "p2p_gatherv": "P2P + Gatherv",
        "allgatherv": "+ Allgatherv",
    }

    fig_h, axes_h = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
    for ax, mode in zip(axes_h.flat, modes):
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0:
            ax.set_title(labels.get(mode, mode))
            continue
        t = np.log10(np.clip(z, 1e-30, None))
        n_edges = edges_from_centers(ns)
        p_edges = edges_from_centers(ps)
        im = ax.pcolormesh(n_edges, p_edges, t, shading="auto", cmap="viridis")
        fig_h.colorbar(im, ax=ax, label=r"$\log_{10}$ time (s)")
        ax.set_xlabel("N")
        ax.set_ylabel("MPI processes")
        ax.set_title(labels.get(mode, mode))
    fig_h.suptitle("Lab 7 matrix multiply — wall time (min over repeats)")
    p = out_dir / "lab7_heatmap_time.png"
    fig_h.savefig(p, dpi=150)
    plt.close(fig_h)
    written.append(p)

    _, _, z_ref = build_grid(rows, "collective_sbg")
    for mode in modes:
        if mode == "collective_sbg":
            continue
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0 or z_ref.size == 0:
            continue
        ratio = z / z_ref
        lr = np.log2(np.clip(ratio, 1e-30, None))
        fig, ax = plt.subplots(figsize=(6.5, 5), constrained_layout=True)
        n_edges = edges_from_centers(ns)
        p_edges = edges_from_centers(ps)
        im = ax.pcolormesh(n_edges, p_edges, lr, shading="auto", cmap="RdBu_r", vmin=-2, vmax=2)
        fig.colorbar(im, ax=ax, label=r"$\log_2$ (time / collective_sbg)")
        ax.set_xlabel("N")
        ax.set_ylabel("MPI processes")
        ax.set_title(f"{labels.get(mode, mode)} / collective_sbg")
        p = out_dir / f"lab7_ratio_vs_sbg_{mode}.png"
        fig.savefig(p, dpi=150)
        plt.close(fig)
        written.append(p)

    fixed_p = [2, 4, 8]
    fig_s, ax_s = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for mode in modes:
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0:
            continue
        p_idx = {int(p): i for i, p in enumerate(ps.tolist())}
        for fp in fixed_p:
            if fp not in p_idx:
                continue
            row = z[p_idx[fp], :]
            ax_s.plot(ns, row, marker="o", label=f"{labels.get(mode, mode)} P={fp}")
    ax_s.set_xlabel("N")
    ax_s.set_ylabel("Time (s)")
    ax_s.set_yscale("log")
    ax_s.set_title("Time vs N (selected P; curves may overlap)")
    ax_s.legend(fontsize=7, ncol=2)
    p = out_dir / "lab7_slice_time_vs_n.png"
    fig_s.savefig(p, dpi=150)
    plt.close(fig_s)
    written.append(p)

    fixed_n = [200, 500, 800]
    fig_p, ax_p = plt.subplots(figsize=(8, 5), constrained_layout=True)
    for mode in modes:
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0:
            continue
        n_idx = {int(n): i for i, n in enumerate(ns.tolist())}
        for fn in fixed_n:
            if fn not in n_idx:
                continue
            col = z[:, n_idx[fn]]
            ax_p.plot(ps, col, marker="o", label=f"{labels.get(mode, mode)} N={fn}")
    ax_p.set_xlabel("MPI processes")
    ax_p.set_ylabel("Time (s)")
    ax_p.set_yscale("log")
    ax_p.set_title("Time vs process count (selected N)")
    ax_p.legend(fontsize=6, ncol=2)
    p = out_dir / "lab7_slice_time_vs_procs.png"
    fig_p.savefig(p, dpi=150)
    plt.close(fig_p)
    written.append(p)

    return written
