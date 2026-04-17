"""Build figures from lab7_bench.csv — readable layout, distinct markers & colors."""

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


def _apply_style():
    import matplotlib.pyplot as plt

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        pass
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.edgecolor": "#333333",
            "axes.linewidth": 0.8,
            "grid.alpha": 0.35,
            "lines.linewidth": 1.8,
            "lines.markersize": 7,
        }
    )


def _algo_markers(modes: list[str]) -> dict[str, str]:
    """One marker shape per algorithm (cycle if more modes than presets)."""
    pool = ("o", "s", "^", "D", "v", "P", "X", "*")
    return {m: pool[i % len(pool)] for i, m in enumerate(modes)}


def _discrete_colors(keys: list[int], cmap_name: str = "tab10"):
    """Stable color per key (e.g. each P or each N)."""
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt

    keys_sorted = sorted(keys)
    n = max(len(keys_sorted), 1)
    cmap = plt.colormaps[cmap_name].resampled(n)
    return {k: mcolors.to_hex(cmap(i / max(n - 1, 1))) for i, k in enumerate(keys_sorted)}


def plot_all(
    csv_path: Path,
    out_dir: Path,
    modes: list[str],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LogNorm, TwoSlopeNorm

    _apply_style()

    rows = load_csv_rows(csv_path)
    if not rows:
        raise ValueError("CSV has no data rows")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    labels = {
        "p2p": "P2P (Send/Recv)",
        "collective_sbg": "Scatterv + Bcast + Gatherv",
        "p2p_gatherv": "P2P + Gatherv",
        "allgatherv": "Scatterv + Bcast + Allgatherv",
    }

    markers = _algo_markers(modes)

    # --- Heatmaps: time in seconds with LogNorm (readable colorbar) ---
    fig_h, axes_h = plt.subplots(2, 2, figsize=(13.5, 10), layout="tight")
    fig_h.suptitle("Wall time (s), best of repeats — darker = slower", y=1.02)
    for ax, mode in zip(axes_h.flat, modes):
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0:
            ax.set_title(labels.get(mode, mode))
            continue
        z_pos = np.clip(z, 1e-9, None)
        vmin = float(np.nanmin(z_pos))
        vmax = float(np.nanmax(z_pos))
        n_edges = edges_from_centers(ns)
        p_edges = edges_from_centers(ps)
        norm = LogNorm(vmin=max(vmin * 0.85, 1e-6), vmax=vmax * 1.05)
        im = ax.pcolormesh(
            n_edges,
            p_edges,
            z_pos,
            shading="auto",
            cmap="YlOrRd",
            norm=norm,
            rasterized=True,
        )
        cb = fig_h.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cb.set_label("seconds")
        ax.set_xlabel("Matrix size N")
        ax.set_ylabel("MPI ranks")
        ax.set_title(labels.get(mode, mode), pad=8)
        ax.set_xticks(ns)
        ax.set_yticks(ps)
    p = out_dir / "lab7_heatmap_time.png"
    fig_h.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig_h)
    written.append(p)

    # --- Ratio vs collective_sbg (single row if 3 modes) ---
    _, _, z_ref = build_grid(rows, "collective_sbg")
    for mode in modes:
        if mode == "collective_sbg":
            continue
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0 or z_ref.size == 0:
            continue
        ratio = z / z_ref
        lr = np.log2(np.clip(ratio, 0.25, 4.0))
        fig, ax = plt.subplots(figsize=(7.2, 5.4), layout="tight")
        n_edges = edges_from_centers(ns)
        p_edges = edges_from_centers(ps)
        norm = TwoSlopeNorm(vmin=-1.5, vcenter=0.0, vmax=1.5)
        im = ax.pcolormesh(
            n_edges,
            p_edges,
            lr,
            shading="auto",
            cmap="RdBu_r",
            norm=norm,
            rasterized=True,
        )
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cb.set_label(r"$\log_2$(time / SBG)")
        ax.set_xlabel("Matrix size N")
        ax.set_ylabel("MPI ranks")
        ax.set_title(
            f"Speed vs reference\n{labels.get(mode, mode)} ÷ Scatterv+Bcast+Gatherv",
            fontsize=11,
        )
        ax.set_xticks(ns)
        ax.set_yticks(ps)
        ax.text(
            0.02,
            0.98,
            "blue = faster\nred = slower",
            transform=ax.transAxes,
            va="top",
            fontsize=9,
            color="#444",
        )
        p = out_dir / f"lab7_ratio_vs_sbg_{mode}.png"
        fig.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        written.append(p)

    # --- Time vs N: one panel per algorithm; color = P, marker = algorithm (constant in panel) ---
    all_ps = sorted({int(r["procs"]) for r in rows})
    p_colors = _discrete_colors(all_ps, "viridis")

    fig_n, axes_n = plt.subplots(2, 2, figsize=(13.5, 10), layout="tight", sharey=True)
    fig_n.suptitle(
        "Time vs matrix size N\n(same marker per panel = one algorithm; line color = MPI rank count)",
        y=1.02,
    )
    handles_p: list = []
    labels_p: list[str] = []
    for ax, mode in zip(axes_n.flat, modes):
        mk = markers[mode]
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0:
            ax.set_title(labels.get(mode, mode))
            continue
        p_idx = {int(p): i for i, p in enumerate(ps.tolist())}
        for p in ps:
            color = p_colors[int(p)]
            row = z[p_idx[int(p)], :]
            line, = ax.plot(
                ns,
                row,
                color=color,
                marker=mk,
                linestyle="-",
                markerfacecolor=color,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=f"P = {p}",
            )
            if mode == modes[0] and ax is axes_n.flat[0]:
                handles_p.append(line)
                labels_p.append(f"P = {p}")
        ax.set_yscale("log")
        ax.set_xlabel("N")
        ax.set_title(labels.get(mode, mode), fontweight="bold")
        ax.grid(True, which="both", alpha=0.35)
    axes_n.flat[0].set_ylabel("Time (s)")
    axes_n.flat[2].set_ylabel("Time (s)")
    if handles_p:
        fig_n.legend(
            handles_p,
            labels_p,
            title="MPI ranks",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=min(len(labels_p), 6),
            frameon=True,
            fancybox=True,
        )
    p = out_dir / "lab7_slice_time_vs_n.png"
    fig_n.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig_n)
    written.append(p)

    # --- Time vs P: one panel per algorithm; color = N, marker = algorithm ---
    all_ns = sorted({int(r["nra"]) for r in rows})
    n_colors = _discrete_colors(all_ns, "plasma")

    fig_p, axes_p = plt.subplots(2, 2, figsize=(13.5, 10), layout="tight", sharey=True)
    fig_p.suptitle(
        "Time vs MPI process count\n(same marker per panel = one algorithm; line color = matrix size N)",
        y=1.02,
    )
    handles_n: list = []
    labels_n: list[str] = []
    for ax, mode in zip(axes_p.flat, modes):
        mk = markers[mode]
        ns, ps, z = build_grid(rows, mode)
        if z.size == 0:
            ax.set_title(labels.get(mode, mode))
            continue
        n_idx = {int(n): i for i, n in enumerate(ns.tolist())}
        for n in ns:
            color = n_colors[int(n)]
            col = z[:, n_idx[int(n)]]
            line, = ax.plot(
                ps,
                col,
                color=color,
                marker=mk,
                linestyle="-",
                markerfacecolor=color,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=f"N = {n}",
            )
            if mode == modes[0] and ax is axes_p.flat[0]:
                handles_n.append(line)
                labels_n.append(f"N = {n}")
        ax.set_yscale("log")
        ax.set_xlabel("MPI ranks")
        ax.set_xticks(ps)
        ax.set_title(labels.get(mode, mode), fontweight="bold")
        ax.grid(True, which="both", alpha=0.35)
    axes_p.flat[0].set_ylabel("Time (s)")
    axes_p.flat[2].set_ylabel("Time (s)")
    if handles_n:
        fig_p.legend(
            handles_n,
            labels_n,
            title="Matrix N",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.02),
            ncol=min(len(labels_n), 6),
            frameon=True,
            fancybox=True,
        )
    p = out_dir / "lab7_slice_time_vs_procs.png"
    fig_p.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig_p)
    written.append(p)

    return written
