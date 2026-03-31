# Plots

Install deps with [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

From the project root (this repo’s `project/` folder):

```bash
uv run python -m plots --input ../results/latest.csv --out ../results/figures
```

Or use `just plot` from the same directory.

Generated PNGs (in `--out`):

1. `01_comparison_sequential_striped_fox.png` — послідовний vs смугастий vs Фокс (час vs n)
2. `02_striped_threads.png` — смугастий: прискорення vs n для різних потоків
3. `03_fox_threads.png` — Фокс: прискорення vs n для різних потоків
4. `04_fox_vs_striped.png` — Фокс vs смугастий при однакових потоках
