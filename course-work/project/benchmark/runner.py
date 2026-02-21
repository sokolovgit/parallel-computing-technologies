"""Benchmark runner: orchestrates runs and produces results."""

from __future__ import annotations

import gc
import statistics
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from benchmark.export import (
    print_bottleneck_analysis,
    print_system_metrics,
    print_table,
    save_csv,
    save_json,
    save_latex_table,
)
from benchmark.models import BenchmarkResult, SystemMetrics
from benchmark.plots import PlotGenerator
from benchmark.stats import HAS_RESOURCE, RunStats, compute_stats, rss_mb

if TYPE_CHECKING:
    from bitonic import ParallelBitonicSorter, SequentialBitonicSorter

if HAS_RESOURCE:
    import resource


def _collect_system_metrics(
    wall_s: float,
    cpu_self_s: float,
    cpu_children_s: float,
    rss_mb_val: float,
    ctx_voluntary: int,
    ctx_involuntary: int,
) -> SystemMetrics:
    return SystemMetrics(
        wall_s=wall_s,
        cpu_self_s=cpu_self_s,
        cpu_children_s=cpu_children_s,
        rss_mb=rss_mb_val,
        ctx_voluntary=ctx_voluntary,
        ctx_involuntary=ctx_involuntary,
    )


class BenchmarkRunner:
    """Orchestrates benchmarking with optional system metrics."""

    def __init__(
        self,
        sizes: list[int] | None = None,
        process_counts: list[int] | None = None,
        num_runs: int = 5,
        warmup_runs: int = 2,
        results_dir: Path | None = None,
        disable_gc: bool = True,
        run_baseline: bool = False,
        run_weak_scaling: bool = False,
        weak_scaling_base: int = 2**14,
    ) -> None:
        self._sizes = sizes or [2**k for k in range(14, 22)]
        self._process_counts = process_counts or [2, 4, 8]
        self._num_runs = num_runs
        self._warmup_runs = warmup_runs
        self._results_dir = (
            results_dir or Path(__file__).resolve().parent.parent / "results"
        )
        self._results_dir.mkdir(exist_ok=True)
        self._disable_gc = disable_gc
        self._run_baseline = run_baseline
        self._run_weak_scaling = run_weak_scaling
        self._weak_scaling_base = weak_scaling_base

    @staticmethod
    def _generate_array(size: int, seed: int = 42) -> NDArray[np.int64]:
        rng = np.random.default_rng(seed)
        return rng.integers(-100_000, 100_000, size=size, dtype=np.int64)

    def _measure_sequential(
        self,
        sorter: SequentialBitonicSorter,
        arr: NDArray[np.int64],
    ) -> tuple[list[float], SystemMetrics | None]:
        from bitonic import SequentialBitonicSorter as _Seq

        assert isinstance(sorter, _Seq)
        for _ in range(self._warmup_runs):
            sorter.sort(arr)
        walls: list[float] = []
        runs_metrics: list[SystemMetrics | None] = []
        for _ in range(self._num_runs):
            if self._disable_gc:
                gc.disable()
            if HAS_RESOURCE:
                r0 = resource.getrusage(resource.RUSAGE_SELF)
                t0_wall = time.perf_counter()
                t0_cpu = time.process_time()
            sorter.sort(arr)
            if HAS_RESOURCE:
                t1_wall = time.perf_counter()
                t1_cpu = time.process_time()
                r1 = resource.getrusage(resource.RUSAGE_SELF)
                wall = t1_wall - t0_wall
                cpu_self = t1_cpu - t0_cpu
                rss = rss_mb(r1.ru_maxrss)
                ctx_v = r1.ru_nvcsw - r0.ru_nvcsw
                ctx_i = r1.ru_nivcsw - r0.ru_nivcsw
                runs_metrics.append(
                    _collect_system_metrics(wall, cpu_self, 0.0, rss, ctx_v, ctx_i)
                )
                walls.append(wall)
            else:
                res = sorter.sort_timed(arr)
                walls.append(res.elapsed)
                runs_metrics.append(None)
            if self._disable_gc:
                gc.enable()
        if HAS_RESOURCE and runs_metrics and walls:
            med = statistics.median(walls)
            idx = min(range(len(walls)), key=lambda i: abs(walls[i] - med))
            return walls, runs_metrics[idx]
        return walls, None

    def _measure_parallel(
        self,
        sorter: ParallelBitonicSorter,
        arr: NDArray[np.int64],
    ) -> tuple[list[float], SystemMetrics | None]:
        from bitonic import ParallelBitonicSorter as _Par

        assert isinstance(sorter, _Par)
        for _ in range(self._warmup_runs):
            sorter.sort(arr)
        walls: list[float] = []
        runs_metrics: list[SystemMetrics | None] = []
        for _ in range(self._num_runs):
            if self._disable_gc:
                gc.disable()
            if HAS_RESOURCE:
                r0 = resource.getrusage(resource.RUSAGE_SELF)
                r0c = resource.getrusage(resource.RUSAGE_CHILDREN)
                t0_wall = time.perf_counter()
                t0_cpu = time.process_time()
            sorter.sort(arr)
            if HAS_RESOURCE:
                t1_wall = time.perf_counter()
                t1_cpu = time.process_time()
                r1 = resource.getrusage(resource.RUSAGE_SELF)
                r1c = resource.getrusage(resource.RUSAGE_CHILDREN)
                wall = t1_wall - t0_wall
                cpu_self = t1_cpu - t0_cpu
                cpu_children = (r1c.ru_utime + r1c.ru_stime) - (
                    r0c.ru_utime + r0c.ru_stime
                )
                rss = rss_mb(r1.ru_maxrss)
                ctx_v = r1.ru_nvcsw - r0.ru_nvcsw
                ctx_i = r1.ru_nivcsw - r0.ru_nivcsw
                runs_metrics.append(
                    _collect_system_metrics(
                        wall, cpu_self, cpu_children, rss, ctx_v, ctx_i
                    )
                )
                walls.append(wall)
            else:
                res = sorter.sort_timed(arr)
                walls.append(res.elapsed)
                runs_metrics.append(None)
            if self._disable_gc:
                gc.enable()
        if HAS_RESOURCE and runs_metrics and walls:
            med = statistics.median(walls)
            idx = min(range(len(walls)), key=lambda i: abs(walls[i] - med))
            return walls, runs_metrics[idx]
        return walls, None

    def _bench_sequential(
        self,
    ) -> tuple[dict[int, list[float]], dict[int, SystemMetrics | None]]:
        from bitonic import SequentialBitonicSorter

        sorter = SequentialBitonicSorter()
        run_times: dict[int, list[float]] = {}
        metrics: dict[int, SystemMetrics | None] = {}
        for size in self._sizes:
            arr = self._generate_array(size)
            walls, m = self._measure_sequential(sorter, arr)
            run_times[size] = walls
            metrics[size] = m
            st = compute_stats(walls)
            print(
                f"  Sequential  n={size:>8,}  "
                f"median={st.median:.4f}s  ±{st.ci_half:.4f}s"
            )
        return run_times, metrics

    def _bench_parallel(
        self,
    ) -> tuple[
        dict[int, dict[int, list[float]]],
        dict[int, dict[int, SystemMetrics | None]],
    ]:
        from bitonic import ParallelBitonicSorter

        run_times: dict[int, dict[int, list[float]]] = {}
        metrics: dict[int, dict[int, SystemMetrics | None]] = {}
        for nprocs in self._process_counts:
            sorter = ParallelBitonicSorter(num_processes=nprocs)
            run_times[nprocs] = {}
            metrics[nprocs] = {}
            for size in self._sizes:
                arr = self._generate_array(size)
                walls, m = self._measure_parallel(sorter, arr)
                run_times[nprocs][size] = walls
                metrics[nprocs][size] = m
                st = compute_stats(walls)
                print(
                    f"  Parallel    n={size:>8,}  procs={nprocs}  "
                    f"median={st.median:.4f}s  ±{st.ci_half:.4f}s"
                )
        return run_times, metrics

    def _bench_baseline(
        self, baseline_sizes: list[int] | None = None
    ) -> tuple[dict[int, list[float]], dict[int, RunStats]]:
        sizes = baseline_sizes or self._sizes
        if len(sizes) > 8:
            idx = [0, len(sizes) // 4, len(sizes) // 2, 3 * len(sizes) // 4, -1]
            sizes = [sizes[i] for i in idx]
        run_times: dict[int, list[float]] = {}
        for size in sizes:
            arr = self._generate_array(size)
            for _ in range(self._warmup_runs):
                np.sort(arr)
            walls = []
            for _ in range(self._num_runs):
                if self._disable_gc:
                    gc.disable()
                t0 = time.perf_counter()
                np.sort(arr.copy())
                walls.append(time.perf_counter() - t0)
                if self._disable_gc:
                    gc.enable()
            run_times[size] = walls
            st = compute_stats(walls)
            print(
                f"  Baseline np.sort  n={size:>8,}  "
                f"median={st.median:.4f}s  ±{st.ci_half:.4f}s"
            )
        stats = {s: compute_stats(times) for s, times in run_times.items()}
        return run_times, stats

    def _bench_weak_scaling(
        self,
    ) -> tuple[
        dict[int, list[float]],
        dict[int, list[float]],
        dict[int, RunStats],
        dict[int, RunStats],
    ]:
        from bitonic import ParallelBitonicSorter, SequentialBitonicSorter

        seq_run_times: dict[int, list[float]] = {}
        par_run_times: dict[int, list[float]] = {}
        base = self._weak_scaling_base
        for nprocs in self._process_counts:
            size = nprocs * base
            arr = self._generate_array(size)
            for _ in range(self._warmup_runs):
                SequentialBitonicSorter().sort(arr)
            walls_seq = []
            for _ in range(self._num_runs):
                if self._disable_gc:
                    gc.disable()
                t0 = time.perf_counter()
                SequentialBitonicSorter().sort(arr)
                walls_seq.append(time.perf_counter() - t0)
                if self._disable_gc:
                    gc.enable()
            seq_run_times[nprocs] = walls_seq
            sorter_par = ParallelBitonicSorter(num_processes=nprocs)
            for _ in range(self._warmup_runs):
                sorter_par.sort(arr)
            walls_par = []
            for _ in range(self._num_runs):
                if self._disable_gc:
                    gc.disable()
                t0 = time.perf_counter()
                sorter_par.sort(arr)
                walls_par.append(time.perf_counter() - t0)
                if self._disable_gc:
                    gc.enable()
            par_run_times[nprocs] = walls_par
            st_seq = compute_stats(walls_seq)
            st_par = compute_stats(walls_par)
            print(
                f"  Weak scaling P={nprocs} n={size:,}  "
                f"seq={st_seq.median:.4f}s  par={st_par.median:.4f}s"
            )
        seq_stats = {p: compute_stats(t) for p, t in seq_run_times.items()}
        par_stats = {p: compute_stats(t) for p, t in par_run_times.items()}
        return seq_run_times, par_run_times, seq_stats, par_stats

    def run(self) -> BenchmarkResult:
        """Execute the full benchmark suite."""
        runs_per = self._warmup_runs + self._num_runs
        print("=" * 60)
        print("Bitonic Sort Benchmark")
        print(f"Sizes:          {[f'{s:,}' for s in self._sizes]}")
        print(f"Process counts: {self._process_counts}")
        print(
            f"Runs per config: {runs_per}"
            f" ({self._warmup_runs} warmup + {self._num_runs} timed)"
        )
        if HAS_RESOURCE:
            print("System metrics: enabled (Unix)")
        else:
            print("System metrics: disabled (Windows or no resource module)")
        print("=" * 60)

        print("\n[1/6] Benchmarking sequential sort...")
        seq_run_times, seq_metrics = self._bench_sequential()

        print("\n[2/6] Benchmarking parallel sort...")
        par_run_times, par_metrics = self._bench_parallel()

        result = BenchmarkResult(
            sequential_run_times=seq_run_times,
            parallel_run_times=par_run_times,
            sequential_metrics=seq_metrics,
            parallel_metrics=par_metrics,
            results_dir=self._results_dir,
        )

        if self._run_baseline:
            print("\n[2b] Baseline (np.sort)...")
            base_run_times, base_stats = self._bench_baseline()
            result.baseline_times = {s: base_stats[s].median for s in base_run_times}
            result.baseline_stats = base_stats

        if self._run_weak_scaling:
            print("\n[2c] Weak scaling...")
            _seq_rt, _par_rt, seq_st, par_st = self._bench_weak_scaling()
            result.weak_scaling_sequential_times = {p: seq_st[p].median for p in seq_st}
            result.weak_scaling_parallel_times = {p: par_st[p].median for p in par_st}
            result.weak_scaling_sequential_stats = seq_st
            result.weak_scaling_parallel_stats = par_st

        print("\n[3/6] Computing speedup & efficiency...")
        result.compute_metrics()
        for nprocs in sorted(result.speedup.keys()):
            for size in sorted(result.speedup[nprocs].keys()):
                sp = result.speedup[nprocs][size]
                eff = result.efficiency[nprocs][size]
                print(
                    f"  procs={nprocs}  n={size:>8,}"
                    f"  speedup={sp:.3f}x  efficiency={eff:.3f}"
                )

        print("\n[4/6] Summary table:")
        print_table(result)

        if HAS_RESOURCE:
            print("\n[5/6] System metrics (representative sizes):")
            print_system_metrics(result)
            print_bottleneck_analysis(result)
        else:
            print("\n[5/6] (Skip system metrics)")

        print("\n[6/6] Generating plots & saving data...")
        PlotGenerator(result).generate_all()
        save_csv(result)
        save_latex_table(result)
        save_json(result)

        print("\nDone!")
        return result
