# Lab 3: Striped and Fox matrix multiplication

Sequential and parallel implementations of square matrix multiply `C = A × B`, a benchmark harness aligned with [../docs/task.txt](../docs/task.txt), and matplotlib plots from exported **CSV**.

## Layout

At the project root, **`matmul/`** (JVM code), **`plots/`** (matplotlib), and **`results/`** (CSV and figures) are **siblings**. The **`matmul/`** tree has **`matmul/src/algorithms/`** (multiply implementations) and **`matmul/src/benchmark/`** (harness, I/O, CLI); **`matmul/out/`** holds compiled classes (gitignored). Java packages stay short (`matrix`, `main`, …) — no `lab3` segment. The `just` recipes set `-Dmatmul.home` to this directory so the default `--out` is always **`results/`** here (not relative to your shell current directory).

| Path | Role |
|------|------|
| `matmul/src/algorithms/matrix/` | `MatrixMultiplier` interface |
| `matmul/src/algorithms/sequential/` | `SequentialMultiplier` |
| `matmul/src/algorithms/parallel/` | `StripedParallelMultiplier`, `FoxParallelMultiplier` |
| `matmul/src/algorithms/util/` | `MatrixOps`, `ExecutorUtils` |
| `matmul/src/benchmark/main/` | `BenchmarkMain` — entrypoint `main.BenchmarkMain` |
| `matmul/src/benchmark/config/` | `BenchmarkConfig` |
| `matmul/src/benchmark/runner/` | `BenchmarkRunner` |
| `matmul/src/benchmark/results/` | `BenchmarkResult` |
| `matmul/src/benchmark/io/` | `ResultsExporter` (CSV) |
| `matmul/src/benchmark/utils/` | `MatrixTestData` |
| `plots/` | `uv` + `matplotlib`; `python -m plots` |
| `results/` | Benchmark output and figures (gitignored except you may commit samples) |

## Prerequisites

- **JDK** (`javac`, `java`) on `PATH`
- **[just](https://github.com/casey/just)** (optional but recommended)
- **[uv](https://github.com/astral-sh/uv)** for Python plots

## Build and verify

```bash
just build
just verify
```

`verify` checks parallel results against sequential multiply for small `n`.

## Benchmark protocol (from the task)

For each configuration:

1. Matrices are filled **outside** timed sections.
2. **Warmup:** one **sequential** multiply (not timed as part of the 20+20).
3. **Parallel:** `runs` timed runs (default **20**), median wall time reported.
4. **Sequential:** `runs` timed runs **after** parallel; median reported.
5. **Speedup** = `median(t_sequential) / median(t_parallel)`.

Algorithms must not print during timed work (no console I/O in hot paths).

**Fox:** uses a `q×q` grid; **thread count must be a perfect square** `q²`. **n** must be divisible by **q** (so each block is `m×m` with `m = n/q`). The CSV column `q` is set for Fox rows; empty for striped.

**Striped:** uses the given thread count (capped to `n` internally so each row has work).

## Commands

```bash
# Full-style run (adjust sizes/threads for your machine)
just benchmark --sizes 512,1024,2048 --threads 4,9,16 --runs 20 --out results

# Report / plots dataset: sequential + striped + Fox; n = 540…1980 step 60; threads 4,9,16; prefix `report`
just benchmark-report

# Plots (Ukrainian figures; expects CSV with sequential, striped, fox rows — use `just benchmark-report` or `--algorithms all`)
just plot
# or
cd plots && uv sync && uv run python -m plots --input ../results/latest.csv --out ../results/figures
```

## Experimental conditions (manual, for the report)

From the assignment: include **only** multiply work in timings (not initialization); **no** console output in algorithms; **20** measurements per reported value; **warmup** with one sequential run; measure **sequential after parallel**; prefer laptop on **AC power**; **disable** internet and unnecessary apps when collecting report-grade numbers.

Document **CPU** (cores logical/physical, frequency) and **OS** in the report; each CSV row includes JVM, OS, and hostname from the harness.

## Implementation notes

- **Striped (row–row):** For each inner index `k`, worker bands update rows of `C` with `a[i][k] * b[k][j]`. This matches the phased accumulation described in the course slides; in shared memory all workers read the same row `b[k]`.
- **Fox:** For steps `k = 0..q-1`, block `(bi,bj)` multiplies `A[bi,(bi+k) mod q]` with `B[(bi+k) mod q,bj]` into `C[bi,bj]`.
