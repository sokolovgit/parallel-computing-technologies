# Benchmark CSV → hierarchical Excel

`csv_to_hierarchical_table.py` читає CSV з `BenchmarkRunner` і будує таблицю з трирівневими заголовками:

1. **Sequential Algorithm** → час послідовного множення (секунди).
2. **Striped Algorithm** / **Fox Algorithm** → для кожної кількості потоків (4, 9, 25): **Time, s** та **Speedup**.

Часи паралельних запусків беруться з `t_parallel_ms` (конвертація в секунди); послідовний — з рядків `algorithm == sequential` (`t_sequential_ms`).

## Запуск

З кореня `lab3/project` (де `justfile`), шляхи — відносно цього каталогу:

```bash
just hierarchical-table ../docs/results/latest.csv results/matrix_table.xlsx
```

Без `just`:

```bash
cd scripts
uv sync
uv run python csv_to_hierarchical_table.py ../../docs/results/latest.csv -o ../../results/matrix_table.xlsx
```

Або `pip install -r requirements.txt` і `python csv_to_hierarchical_table.py …`.
