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
      stats.py                    # RunStats, compute_stats
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

Generates three plots in `results/`:

- `execution_time.png` -- execution time vs input size
- `speedup_vs_size.png` -- speedup vs input size for different process counts
- `speedup_vs_processes.png` -- speedup vs number of processes for selected input sizes
- `benchmark_data.json` -- raw timing data

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
