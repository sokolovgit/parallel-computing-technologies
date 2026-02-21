"""Plot generation for benchmark results."""

from __future__ import annotations

import matplotlib.pyplot as plt

from benchmark.models import BenchmarkResult
from benchmark.stats import HAS_RESOURCE, speedup_ci_half


class PlotGenerator:
    """Generates all benchmark plots from a BenchmarkResult."""

    def __init__(self, result: BenchmarkResult) -> None:
        self._result = result
        self._dir = result.results_dir

    def plot_execution_time(self) -> None:
        result = self._result
        sizes = sorted(result.sequential_times.keys())
        fig, ax = plt.subplots(figsize=(10, 6))

        seq_meds = [result.sequential_times[s] for s in sizes]
        seq_errs = [
            result.sequential_stats[s].ci_half if s in result.sequential_stats else 0.0
            for s in sizes
        ]
        ax.errorbar(
            sizes,
            seq_meds,
            yerr=seq_errs,
            marker="o",
            label="Sequential",
            linewidth=2,
            capsize=2,
        )
        for nprocs in sorted(result.parallel_times.keys()):
            meds = [result.parallel_times[nprocs][s] for s in sizes]
            errs = [
                result.parallel_stats.get(nprocs, {}).get(s)
                and result.parallel_stats[nprocs][s].ci_half
                or 0.0
                for s in sizes
            ]
            ax.errorbar(
                sizes,
                meds,
                yerr=errs,
                marker="s",
                label=f"Parallel ({nprocs} procs)",
                linewidth=2,
                capsize=2,
            )

        ax.set_xlabel("Input size (n)")
        ax.set_ylabel("Time (seconds)")
        ax.set_title("Bitonic Sort: Execution Time vs Input Size")
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = self._dir / "execution_time.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def plot_speedup(self) -> None:
        result = self._result
        fig, ax = plt.subplots(figsize=(10, 6))
        for nprocs in sorted(result.speedup.keys()):
            sizes = sorted(result.speedup[nprocs].keys())
            sp_meds = [result.speedup[nprocs][s] for s in sizes]
            sp_errs = []
            for s in sizes:
                seq_st = result.sequential_stats.get(s)
                par_st = result.parallel_stats.get(nprocs, {}).get(s)
                sp_errs.append(
                    speedup_ci_half(seq_st, par_st) if seq_st and par_st else 0.0
                )
            ax.errorbar(
                sizes,
                sp_meds,
                yerr=sp_errs,
                marker="s",
                label=f"{nprocs} processes",
                linewidth=2,
                capsize=2,
            )
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.7, label="Speedup = 1")
        ax.set_xlabel("Input size (n)")
        ax.set_ylabel("Speedup (T_seq / T_par)")
        ax.set_title("Bitonic Sort: Speedup vs Input Size")
        ax.set_xscale("log", base=2)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = self._dir / "speedup_vs_size.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def plot_speedup_vs_processes(
        self, highlight_sizes: list[int] | None = None
    ) -> None:
        result = self._result
        all_sizes = sorted(next(iter(result.speedup.values())).keys())
        if highlight_sizes is None:
            highlight_sizes = [all_sizes[len(all_sizes) // 2], all_sizes[-1]]
        nprocs_list = sorted(result.speedup.keys())
        fig, ax = plt.subplots(figsize=(10, 6))
        for size in highlight_sizes:
            sp_meds = [result.speedup[np_][size] for np_ in nprocs_list]
            sp_errs = []
            seq_st = result.sequential_stats.get(size)
            for np_ in nprocs_list:
                par_st = result.parallel_stats.get(np_, {}).get(size)
                sp_errs.append(
                    speedup_ci_half(seq_st, par_st) if seq_st and par_st else 0.0
                )
            ax.errorbar(
                nprocs_list,
                sp_meds,
                yerr=sp_errs,
                marker="o",
                label=f"n = {size:,}",
                linewidth=2,
                capsize=2,
            )
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.7, label="Speedup = 1")
        ax.set_xlabel("Number of processes")
        ax.set_ylabel("Speedup (T_seq / T_par)")
        ax.set_title("Bitonic Sort: Speedup vs Number of Processes")
        ax.set_xticks(nprocs_list)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = self._dir / "speedup_vs_processes.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def plot_efficiency(self) -> None:
        result = self._result
        fig, ax = plt.subplots(figsize=(10, 6))
        for nprocs in sorted(result.efficiency.keys()):
            sizes = sorted(result.efficiency[nprocs].keys())
            eff_meds = [result.efficiency[nprocs][s] for s in sizes]
            eff_errs = []
            for s in sizes:
                seq_st = result.sequential_stats.get(s)
                par_st = result.parallel_stats.get(nprocs, {}).get(s)
                sp_ci = speedup_ci_half(seq_st, par_st) if seq_st and par_st else 0.0
                eff_errs.append(sp_ci / nprocs if nprocs else 0.0)
            ax.errorbar(
                sizes,
                eff_meds,
                yerr=eff_errs,
                marker="s",
                label=f"{nprocs} processes",
                linewidth=2,
                capsize=2,
            )
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.7, label="Ideal")
        ax.set_xlabel("Input size (n)")
        ax.set_ylabel("Efficiency (Speedup / P)")
        ax.set_title("Bitonic Sort: Parallel Efficiency (theoretical max = 1)")
        ax.set_xscale("log", base=2)
        ax.set_ylim(bottom=0)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = self._dir / "efficiency.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def plot_cpu_utilization(self) -> None:
        if not HAS_RESOURCE or not self._result.parallel_metrics:
            return
        result = self._result
        fig, ax = plt.subplots(figsize=(10, 6))
        for nprocs in sorted(result.parallel_metrics.keys()):
            sizes = sorted(result.parallel_metrics[nprocs].keys())
            utils = [
                result.parallel_metrics[nprocs][s].cpu_utilization(nprocs)
                if result.parallel_metrics[nprocs][s]
                else 0.0
                for s in sizes
            ]
            ax.plot(sizes, utils, marker="s", label=f"{nprocs} procs", linewidth=2)
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.7, label="Ideal")
        ax.set_xlabel("Input size (n)")
        ax.set_ylabel("CPU utilization (child CPU / (wall × P))")
        ax.set_title("Bitonic Sort: Parallel CPU Utilization")
        ax.set_xscale("log", base=2)
        ax.set_ylim(bottom=0)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = self._dir / "cpu_utilization.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def plot_baseline_comparison(self) -> None:
        result = self._result
        if not result.baseline_times:
            return
        sizes = sorted(set(result.baseline_times) & set(result.sequential_times))
        if not sizes:
            return
        fig, ax = plt.subplots(figsize=(10, 6))
        seq_meds = [result.sequential_times.get(s, 0) for s in sizes]
        seq_errs = [
            result.sequential_stats[s].ci_half if s in result.sequential_stats else 0.0
            for s in sizes
        ]
        base_meds = [result.baseline_times[s] for s in sizes]
        base_errs = [
            result.baseline_stats[s].ci_half if s in result.baseline_stats else 0.0
            for s in sizes
        ]
        x = range(len(sizes))
        w = 0.35
        ax.bar(
            [i - w / 2 for i in x],
            seq_meds,
            w,
            yerr=seq_errs,
            label="Sequential bitonic",
            capsize=2,
        )
        ax.bar(
            [i + w / 2 for i in x],
            base_meds,
            w,
            yerr=base_errs,
            label="np.sort",
            capsize=2,
        )
        ax.set_xticks(x)
        ax.set_xticklabels([f"{s:,}" for s in sizes])
        ax.set_xlabel("Input size (n)")
        ax.set_ylabel("Time (seconds)")
        ax.set_title("Bitonic Sort: Sequential vs np.sort Baseline")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")
        fig.tight_layout()
        path = self._dir / "baseline_comparison.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def plot_weak_scaling(self) -> None:
        result = self._result
        if not result.weak_scaling_parallel_times:
            return
        nprocs_list = sorted(result.weak_scaling_parallel_times.keys())
        fig, ax = plt.subplots(figsize=(10, 6))
        seq_meds = [result.weak_scaling_sequential_times.get(p, 0) for p in nprocs_list]
        seq_errs = [
            result.weak_scaling_sequential_stats.get(p).ci_half
            if result.weak_scaling_sequential_stats.get(p)
            else 0.0
            for p in nprocs_list
        ]
        par_meds = [result.weak_scaling_parallel_times[p] for p in nprocs_list]
        par_errs = [
            result.weak_scaling_parallel_stats.get(p).ci_half
            if result.weak_scaling_parallel_stats.get(p)
            else 0.0
            for p in nprocs_list
        ]
        ax.errorbar(
            nprocs_list,
            seq_meds,
            yerr=seq_errs,
            marker="o",
            label="Sequential",
            linewidth=2,
            capsize=2,
        )
        ax.errorbar(
            nprocs_list,
            par_meds,
            yerr=par_errs,
            marker="s",
            label="Parallel",
            linewidth=2,
            capsize=2,
        )
        ax.set_xlabel("Number of processes (P); n = P × base")
        ax.set_ylabel("Time (seconds)")
        ax.set_title("Bitonic Sort: Weak Scaling (constant work per process)")
        ax.set_xticks(nprocs_list)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        path = self._dir / "weak_scaling.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"  Saved {path}")

    def generate_all(self) -> None:
        """Generate all applicable plots."""
        self.plot_execution_time()
        self.plot_speedup()
        self.plot_speedup_vs_processes()
        self.plot_efficiency()
        self.plot_cpu_utilization()
        if self._result.baseline_times:
            self.plot_baseline_comparison()
        if self._result.weak_scaling_parallel_times:
            self.plot_weak_scaling()
