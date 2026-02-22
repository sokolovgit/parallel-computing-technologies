# Bitonic Sort

Parallel implementation of the Bitonic Sort algorithm in Python using `multiprocessing` and `numpy`.

Course work for "Parallel Computing Technologies" (KPI, 2026).

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager
- [just](https://github.com/casey/just) command runner

## Installation

```bash
cd course-work/project
uv sync
```

This creates a `.venv` and installs all dependencies (numpy, matplotlib, ruff, mypy, pytest).

## Project Structure

```
project/
  pyproject.toml
  src/
    bitonic/                       # Bitonic sort package
      __init__.py                  # Public API
      base.py                      # BitonicSorter base + SortResult
      sequential.py                # SequentialBitonicSorter
      parallel.py                  # ParallelBitonicSorter (SharedMemory)
  benchmark/                       # Benchmark package (sibling to src, tests)
      __init__.py
      __main__.py                  # Entry: python -m benchmark
      models.py                   # BenchmarkResult, SystemMetrics
      stats.py                    # RunStats, compute_stats, filter_outliers_iqr
      plot_style.py               # Shared plot style, palette, size formatter
      plots.py                    # PlotGenerator
      export.py                   # CSV, JSON, LaTeX, console output
      runner.py                   # BenchmarkRunner
  tests/
    test_bitonic_sort.py           # Correctness tests (36 tests)
  results/                         # Generated benchmark plots and data
```

Run the sort from the project root with `src` on `PYTHONPATH`, or from inside `src`:

```python
import numpy as np
# From project root (e.g. in tests): sys.path.insert(0, "src")
from bitonic import SequentialBitonicSorter

sorter = SequentialBitonicSorter()
result = sorter.sort(np.array([10, 30, 11, 20, 4, 330, 21, 110]))
# array([4, 10, 11, 20, 21, 30, 110, 330])
```

```python
from bitonic import ParallelBitonicSorter

sorter = ParallelBitonicSorter(num_processes=4)
result = sorter.sort([10, 30, 11, 20, 4, 330, 21, 110])
# array([4, 10, 11, 20, 21, 30, 110, 330])

# With timing
sort_result = sorter.sort_timed([10, 30, 11, 20])
print(sort_result.data, sort_result.elapsed)
```

### Running benchmarks

```bash
just benchmark
```

This runs the default benchmark (sizes 2^14–2^21, process counts 2/4/8) and writes plots and data to `results/`.

**Reproducibility:** Input arrays are generated with a fixed random seed (42), so repeated runs on the same machine are comparable.

**CLI options** (when running `uv run python -m benchmark`):

- `--num-runs N` — number of timed runs per config (default: 5, or set `BENCH_NUM_RUNS`)
- `--warmup N` — warmup runs per config (default: 2, or set `BENCH_WARMUP_RUNS`)
- `--drop-outliers` — remove outliers with IQR (1.5×) before computing median and CI
- `--format png,svg,pdf` — output format(s) for plots (default: png)
- `--baseline` — also run `np.sort` baseline comparison
- `--weak-scaling` — also run weak scaling benchmarks

**Outputs in `results/`:**

- `execution_time.*` — execution time vs input size
- `speedup_vs_size.*` — speedup vs input size per process count
- `speedup_vs_processes.*` — speedup vs number of processes (selected sizes)
- `efficiency.*` — parallel efficiency
- `cpu_utilization.*` — CPU utilization (Unix only)
- `baseline_comparison.*`, `weak_scaling.*` — when `--baseline` / `--weak-scaling` are used
- `benchmark_data.json`, `benchmark_times.csv`, `table.tex` — raw data and LaTeX table


## Development

### Tests

```bash
just test
```

### Linting

```bash
just lint
```

### Formatting

```bash
just format
```

### Type checking

```bash
just typecheck
```

### Run all checks

```bash
just check
```

### List all available recipes

```bash
just --list
```
