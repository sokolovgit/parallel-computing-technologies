from __future__ import annotations

import gc
import statistics
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from benchmark.config import BenchmarkConfig
from benchmark.export import (
    print_table,
    save_csv,
    save_json,
    save_latex_table,
)
from benchmark.models import BenchmarkResult, SystemMetrics
from benchmark.plots import PlotGenerator
from benchmark.stats import (
    HAS_RESOURCE,
    RunStats,
    compute_stats,
    filter_outliers_iqr,
    rss_mb,
)

if TYPE_CHECKING:
    from bitonic import ParallelBitonicSorter, SequentialBitonicSorter

if HAS_RESOURCE:
    import resource


def run_trials(
    fn: Callable[[], None],
    *,
    warmup_runs: int,
    num_runs: int,
    drop_outliers: bool = False,
    disable_gc: bool = True,
    track_system_metrics: bool = False,
) -> tuple[list[float], RunStats, SystemMetrics | None]:
    for _ in range(warmup_runs):
        fn()
    walls: list[float] = []
    runs_metrics: list[SystemMetrics | None] = []
    for _ in range(num_runs):
        if disable_gc:
            gc.disable()
        if HAS_RESOURCE and track_system_metrics:
            r0 = resource.getrusage(resource.RUSAGE_SELF)
            r0c = resource.getrusage(resource.RUSAGE_CHILDREN)
            t0_wall = time.perf_counter()
            t0_cpu = time.process_time()
            fn()
            t1_wall = time.perf_counter()
            t1_cpu = time.process_time()
            r1 = resource.getrusage(resource.RUSAGE_SELF)
            r1c = resource.getrusage(resource.RUSAGE_CHILDREN)
            wall = t1_wall - t0_wall
            cpu_self = t1_cpu - t0_cpu
            cpu_children = (r1c.ru_utime + r1c.ru_stime) - (r0c.ru_utime + r0c.ru_stime)
            rss = rss_mb(r1.ru_maxrss)
            ctx_v = r1.ru_nvcsw - r0.ru_nvcsw
            ctx_i = r1.ru_nivcsw - r0.ru_nivcsw
            runs_metrics.append(
                _collect_system_metrics(wall, cpu_self, cpu_children, rss, ctx_v, ctx_i)
            )
            walls.append(wall)
        else:
            t0 = time.perf_counter()
            fn()
            walls.append(time.perf_counter() - t0)
        if disable_gc:
            gc.enable()
    rep_metric: SystemMetrics | None = None
    if HAS_RESOURCE and track_system_metrics and runs_metrics and walls:
        med = statistics.median(walls)
        idx = min(range(len(walls)), key=lambda i: abs(walls[i] - med))
        rep_metric = runs_metrics[idx]
    if drop_outliers and len(walls) >= 4:
        walls = filter_outliers_iqr(walls)
    stats = compute_stats(walls)
    return walls, stats, rep_metric


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
    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        self._config = config or BenchmarkConfig.default()
        self._config.results_dir.mkdir(exist_ok=True)

    @staticmethod
    def _generate_array(size: int, seed: int = 42) -> NDArray[np.int64]:
        rng = np.random.default_rng(seed)
        return rng.integers(-100_000, 100_000, size=size, dtype=np.int64)

    def _measure(
        self,
        run_one: Callable[[], None],
        track_system_metrics: bool = False,
    ) -> tuple[list[float], RunStats, SystemMetrics | None]:
        return run_trials(
            run_one,
            warmup_runs=self._config.warmup_runs,
            num_runs=self._config.num_runs,
            drop_outliers=self._config.drop_outliers,
            disable_gc=self._config.disable_gc,
            track_system_metrics=track_system_metrics and HAS_RESOURCE,
        )

    def _measure_sequential(
        self,
        sorter: SequentialBitonicSorter,
        arr: NDArray[np.int64],
    ) -> tuple[list[float], RunStats, SystemMetrics | None]:
        from bitonic import SequentialBitonicSorter as _Seq

        assert isinstance(sorter, _Seq)
        return self._measure(lambda: sorter.sort(arr), track_system_metrics=False)

    def _measure_parallel(
        self,
        sorter: ParallelBitonicSorter,
        arr: NDArray[np.int64],
    ) -> tuple[list[float], RunStats, SystemMetrics | None]:
        from bitonic import ParallelBitonicSorter as _Par

        assert isinstance(sorter, _Par)
        return self._measure(lambda: sorter.sort(arr), track_system_metrics=True)

    def _bench_sequential(
        self,
    ) -> tuple[dict[int, list[float]], dict[int, SystemMetrics | None]]:
        from bitonic import SequentialBitonicSorter

        sorter = SequentialBitonicSorter()
        run_times: dict[int, list[float]] = {}
        metrics: dict[int, SystemMetrics | None] = {}
        for size in self._config.sizes:
            arr = self._generate_array(size)
            walls, st, m = self._measure_sequential(sorter, arr)
            run_times[size] = walls
            metrics[size] = m
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
        for nprocs in self._config.process_counts:
            run_times[nprocs] = {}
            metrics[nprocs] = {}
            sorter = ParallelBitonicSorter(num_processes=nprocs)
            for size in self._config.sizes:
                arr = self._generate_array(size)
                walls, st, m = self._measure_parallel(sorter, arr)
                run_times[nprocs][size] = walls
                metrics[nprocs][size] = m
                print(
                    f"  Parallel    n={size:>8,}  procs={nprocs}  "
                    f"median={st.median:.4f}s  ±{st.ci_half:.4f}s"
                )
        return run_times, metrics

    def run(self) -> BenchmarkResult:
        runs_per = self._config.warmup_runs + self._config.num_runs
        print("=" * 60)
        print("Bitonic Sort Benchmark")
        print(f"Sizes:          {[f'{s:,}' for s in self._config.sizes]}")
        print(f"Process counts: {self._config.process_counts}")
        print(
            f"Runs per config: {runs_per}"
            f" ({self._config.warmup_runs} warmup + {self._config.num_runs} timed)"
        )
        if self._config.drop_outliers:
            print("Outlier removal: IQR (1.5×) before computing stats")
        print("=" * 60)

        print("\n[1/2] Benchmarking sequential sort...")
        seq_run_times, seq_metrics = self._bench_sequential()

        print("\n[2/2] Benchmarking parallel sort...")
        par_run_times, par_metrics = self._bench_parallel()

        result = BenchmarkResult(
            sequential_run_times=seq_run_times,
            parallel_run_times=par_run_times,
            sequential_metrics=seq_metrics,
            parallel_metrics=par_metrics,
            results_dir=self._config.results_dir,
        )

        print("\nComputing speedup & efficiency...")
        result.compute_metrics()
        for nprocs in sorted(result.speedup.keys()):
            for size in sorted(result.speedup[nprocs].keys()):
                sp = result.speedup[nprocs][size]
                eff = result.efficiency[nprocs][size]
                print(
                    f"  procs={nprocs}  n={size:>8,}"
                    f"  speedup={sp:.3f}x  efficiency={eff:.3f}"
                )

        print("\nSummary table:")
        print_table(result)

        print("\nGenerating plots & saving data...")
        PlotGenerator(result, formats=self._config.plot_formats).generate_all()
        save_csv(result)
        save_latex_table(result)
        save_json(result)

        print("\nDone!")
        return result
