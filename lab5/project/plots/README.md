# lab5 plots

`Task1Benchmark` writes CSV under `results/`. From `lab5/project` run **`just task1-plots`** (benchmark + figures).

To regenerate figures only from existing CSV (manual):

```bash
cd lab5/project/plots
uv sync
uv run python -m lab5_plots --by-load ../results/lab5_by_load.csv --by-queue ../results/lab5_by_queue.csv --out ../results/figures_task1
```
