# Практикум 7 — MPI колективи, множення матриць (mpi4py + numpy)

Потрібні **Open MPI** (`mpirun`) і **Python 3.10+** з [uv](https://docs.astral.sh/uv/).

## Команди

1. **Демонстрація коректності** (усі варіанти алгоритмів, малий `N`):

```bash
cd lab7/project
just demo
```

Еквівалентно: `mpirun -np 4 uv run python -m benchmarks.demo` після `uv sync`.

2. **Бенчмарк і графіки** (параметри в `benchmarks/run_benchmarks.py`):

```bash
cd lab7/project
just bench-plot
```

Результати: `lab7/docs/results/lab7_bench.csv` та PNG.

## Структура

- `src/matrix_multiplication/` — `base.py`, `partition.py`, `registry.py` (`ALGOS`), підпакет `implementations/` з класами `p2p`, `collective_sbg`, `p2p_gatherv`, `allgatherv`.
- `benchmarks/` — `demo.py`, `bench_runner.py` (один MPI-прогін), `run_benchmarks.py` (сітка + CSV + виклик графіків).
- `plots/figures.py` — побудова matplotlib.
- Звіт: `lab7/docs/report/lab7.md`.
